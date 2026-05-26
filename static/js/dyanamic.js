document.addEventListener('DOMContentLoaded', function () {
    const seeMoreButtons = document.querySelectorAll('.see-more-btn');

    seeMoreButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            
            const targetCardId = this.getAttribute('data-target');
            const targetCard = document.getElementById(targetCardId);
            
            if (targetCard) {
                const hiddenRows = targetCard.querySelectorAll('.table-row-hidden');
                
                hiddenRows.forEach(row => {
                    // Toggles display between 'table-row' and 'none'
                    row.style.display = (row.style.display === 'table-row') ? 'none' : 'table-row';
                });

                // Toggles the button text
                if (this.textContent === 'See All') {
                    this.textContent = 'Show Less';
                } else {
                    this.textContent = 'See All';
                }
            }
        });
    });
});


document.getElementById("HMSSearchInput").addEventListener("keyup", function () {
    const filter = this.value.toLowerCase();
    const rows = document.querySelectorAll("#HMSTable tr");
    rows.forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(filter) ? "" : "none";
    });
});


// Appointment Booking Modal Date Validation

document.addEventListener('DOMContentLoaded', function () {
    var bookingModal = document.getElementById('bookingModal');
    var dateInput = document.getElementById('appointment_date');
    var requiredDayName = ""; // Yahan hum store karenge ki user ne konsa din click kiya (e.g., 'Monday')

    // Day Name ko Number me convert karne ke liye map (Sunday=0, Monday=1, etc.)
    const dayMap = {
        'Sunday': 0,
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6
    };

    // 1. Jab Modal Khulega
    bookingModal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget;
        
        // Data fetch kar rahe hain button se
        requiredDayName = button.getAttribute('data-day'); // e.g., "Monday"
        var slot = button.getAttribute('data-slot'); 
        var startTime = button.getAttribute('data-time');

        // Modal ke text update karo
        document.getElementById('modalDayDisplay').textContent = requiredDayName;
        document.getElementById('modalDayHint').textContent = requiredDayName;
        document.getElementById('modalSlotDisplay').textContent = slot;
        document.getElementById('modalSlotTime').value = startTime;

        // Purani date clear kar do taaki user fresh select kare
        dateInput.value = "";
    });

    // 2. Jab User Date Change karega (Validation Logic)
    dateInput.addEventListener('change', function() {
        var inputDate = new Date(this.value);
        
        // Note: Kabhi kabhi timezone ki wajah se date 1 din piche ho jati hai JS me
        // Isliye hum day index nikaalne ke liye thoda safe method use karenge
        var dayIndex = inputDate.getDay(); 

        var requiredIndex = dayMap[requiredDayName];

        // Agar din match nahi hua
        if (dayIndex !== requiredIndex) {
            alert("Incorrect Date! Please select a date that is a " + requiredDayName + ".");
            this.value = ""; // Galat date ko hata do
        }
    });
});

