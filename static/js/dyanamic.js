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

