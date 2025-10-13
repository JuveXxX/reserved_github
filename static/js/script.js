// Logique de la réservation

document.addEventListener("DOMContentLoaded", () =>{
	const seats= document.querySelectorAll(".seat");
	const selectedList= document.getElementById('selected-list');
	const inputSeats= document.getElementById('selected-seats');

	let selectedSeats= [];
	seats.forEach(seat =>{
		seat.addEventListener("click", ()=>{
			if (seat.classList.contains("reserved")) return;
			seat.classList.toggle("selected");
			const seatId= seat.dataset.seat;
			if (selectedSeats.includes(seatId)) {
				selectedSeats= selectedSeats.filter(s => s !== seatId);
			}
			else{
				selectedSeats.push(seatId);
			}

			// Affichage de la liste des sièges sélectionnés
			selectedList.textContent= selectedSeats.length > 0 ? selectedSeats.join(", "):"Aucun";

			// Envoi au backend
			inputSeats.value= selectedSeats.join(",");
		});
	});
});