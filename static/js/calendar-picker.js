/* ============================================================
   HMS Portal - Interactive Calendar Slot Picker JS
   Receives doctor weekly schedule + booked datetimes from server.
   Also receives daily capacity info (Feature 2).
   ============================================================ */
(function () {
    'use strict';

    window.initCalendarPicker = function (options) {
        var container = document.getElementById(options.containerId);
        if (!container) return;

        var schedule = options.schedule || {};       // { "Monday": ["08:00:00", "16:00:00"], ... }
        var bookedDates = options.bookedDates || [];  // ["2025-01-15 08:00:00", ...]
        var doctorId = options.doctorId;
        var csrfToken = options.csrfToken;
        var capacityMap = options.capacityMap || {};  // { "2025-01-15": 3 } booked count per date
        var maxPerDay = options.maxPerDay || 20;      // daily capacity ceiling

        var selectedDate = null;

        // Normalize schedule into day -> [start times]
        var daySlots = {};
        Object.keys(schedule).forEach(function (day) {
            var slots = [];
            if (schedule[day] && schedule[day].length) {
                schedule[day].forEach(function (t) {
                    slots.push(t.slice(0, 5)); // "08:00:00" -> "08:00"
                });
            }
            daySlots[day] = slots;
        });

        var booked = new Set(bookedDates.map(function (d) { return d.substring(0, 16); }));

        var now = new Date();
        var currentMonth = new Date(now.getFullYear(), now.getMonth(), 1);

        function monthName(date) {
            return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        }

        function pad(n) { return n < 10 ? '0' + n : '' + n; }

        function dateKey(date) {
            return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate());
        }

        function isDayFull(cellKey) {
            return (capacityMap[cellKey] || 0) >= maxPerDay;
        }

        function buildCalendar() {
            var gridHtml = '<div class="cal-header"><button onclick="window.calPrev()"><i class="bi bi-chevron-left"></i></button>'
                + '<h6>' + monthName(currentMonth) + '</h6>'
                + '<button onclick="window.calNext()"><i class="bi bi-chevron-right"></i></button></div>';
            gridHtml += '<div class="cal-grid">';
            ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].forEach(function (d) {
                gridHtml += '<div class="cal-day-header">' + d + '</div>';
            });

            var firstDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
            var startOffset = firstDay.getDay();
            var startDate = new Date(firstDay);
            startDate.setDate(startDate.getDate() - startOffset);

            for (var i = 0; i < 42; i++) {
                var cell = new Date(startDate);
                cell.setDate(startDate.getDate() + i);
                var inMonth = cell.getMonth() === currentMonth.getMonth();
                var classes = ['cal-day'];
                if (!inMonth) classes.push('other-month');
                var todayKey = dateKey(now);
                var cellKey = dateKey(cell);
                if (cellKey === todayKey) classes.push('today');
                if (selectedDate && cellKey === dateKey(selectedDate)) classes.push('selected');

                var isFuture = cell >= new Date(now.getFullYear(), now.getMonth(), now.getDate());
                var dayName = cell.toLocaleDateString('en-US', { weekday: 'long' });
                var hasSlots = isFuture && daySlots[dayName] && daySlots[dayName].length > 0;
                var dayFull = isFuture && hasSlots && isDayFull(cellKey);

                if (hasSlots && !dayFull) classes.push('available');
                else if (hasSlots && dayFull) classes.push('full');
                else classes.push('unavailable');

                gridHtml += '<div class="' + classes.join(' ') + '" data-date="' + cellKey + '" data-full="' + (dayFull ? '1' : '0') + '">' + cell.getDate() + '</div>';
            }
            gridHtml += '</div>';
            container.innerHTML = gridHtml;

            container.querySelectorAll('.cal-day.available').forEach(function (el) {
                el.addEventListener('click', function () {
                    var parts = this.getAttribute('data-date').split('-');
                    selectedDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
                    buildCalendar();
                    renderSlots();
                });
            });

            container.querySelectorAll('.cal-day.full').forEach(function (el) {
                el.addEventListener('click', function () {
                    if (typeof window.showToast === 'function') {
                        window.showToast('This day is fully booked (' + maxPerDay + '/' + maxPerDay + '). Pick another day.', 'warning');
                    }
                });
            });
        }

        function renderSlots() {
            var slotsArea = document.getElementById(options.slotsId);
            if (!slotsArea) return;
            if (!selectedDate) {
                slotsArea.innerHTML = '<p class="text-muted mb-0" style="font-size:.85rem;">Select a date from the calendar above.</p>';
                return;
            }
            var dayName = selectedDate.toLocaleDateString('en-US', { weekday: 'long' });
            var times = daySlots[dayName] || [];
            var key = dateKey(selectedDate);
            var available = times.filter(function (t) {
                var dt = key + ' ' + t;
                return !booked.has(dt) && new Date(key + 'T' + t) > new Date();
            });
            if (available.length === 0) {
                slotsArea.innerHTML = '<h6>No available slots on ' + dayName + '.</h6>';
                return;
            }
            var bookedCount = capacityMap[key] || 0;
            var html = '<div class="d-flex justify-content-between align-items-center mb-2">'
                + '<h6 class="mb-0">Available slots on ' + selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' }) + '</h6>'
                + '<span class="badge badge-info">' + bookedCount + '/' + maxPerDay + ' booked</span></div>';
            available.forEach(function (t) {
                var display = new Date('2000-01-01T' + t).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
                html += '<button type="button" class="slot-btn" data-time="' + t + ':00">' + display + '</button>';
            });
            slotsArea.innerHTML = html;

            slotsArea.querySelectorAll('.slot-btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    slotsArea.querySelectorAll('.slot-btn').forEach(function (b) { b.classList.remove('selected'); });
                    this.classList.add('selected');
                    document.getElementById('slot_time').value = this.getAttribute('data-time');
                    document.getElementById('appointment_date').value = dateKey(selectedDate);
                });
            });
        }

        window.calPrev = function () { currentMonth.setMonth(currentMonth.getMonth() - 1); buildCalendar(); };
        window.calNext = function () { currentMonth.setMonth(currentMonth.getMonth() + 1); buildCalendar(); };

        buildCalendar();
    };
})();