function displayTime() {
	let element = document.getElementById("clock"); // Найти элемент с id="clock" 
	let now = new Date();    // Получить текущее время
	element.innerHTML = now.toLocaleTimeString(); // Отобразить время
	setTimeout(displayTime, 1000);    // Вызывать функцию каждую секунду
}
window.onload = displayTime; // Начать отображение времени после загрузки документа