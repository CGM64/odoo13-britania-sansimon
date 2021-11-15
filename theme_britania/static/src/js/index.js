const fila = document.querySelector('.contenedor-carousel');
const customitemss = document.querySelectorAll('.custom-carousel-item');

const flechaIzquierda = document.getElementById('flecha-izquierda');
const flechaDerecha = document.getElementById('flecha-derecha');

// ? ----- ----- Event Listener para la flecha derecha. ----- -----
if (flechaDerecha) {
	flechaDerecha.addEventListener('click', () => {
		fila.scrollLeft += fila.offsetWidth;

		// const indicadorActivo = document.querySelector('.indicadores .activo');
		// if (indicadorActivo && indicadorActivo.nextSibling) {
		// 	indicadorActivo.nextSibling.classList.add('activo');
		// 	indicadorActivo.classList.remove('activo');
		// }
	});
}

// ? ----- ----- Event Listener para la flecha izquierda. ----- -----
if (flechaIzquierda) {
	flechaIzquierda.addEventListener('click', () => {
		fila.scrollLeft -= fila.offsetWidth;

		// const indicadorActivo = document.querySelector('.indicadores .activo');
		// if (indicadorActivo && indicadorActivo.previousSibling) {
		// 	indicadorActivo.previousSibling.classList.add('activo');
		// 	indicadorActivo.classList.remove('activo');
		// }
	});
}

// ? ----- ----- Paginacion ----- -----
// const numeroPaginas = Math.ceil(customitemss.length / 3);
// for (let i = 0; i < numeroPaginas; i++) {
// 	const indicador = document.createElement('button');

// 	if (indicador && i === 0) {
// 		indicador.classList.add('activo');
// 	}

// 	if (indicador) {
// 		document.querySelector('.indicadores').appendChild(indicador);
// 		indicador.addEventListener('click', (e) => {
// 			fila.scrollLeft = i * fila.offsetWidth;

// 			document.querySelector('.indicadores .activo').classList.remove('activo');
// 			e.target.classList.add('activo');
// 		});
// 	}
// }

// ? ----- ----- Hover ----- -----
customitemss.forEach((customitems) => {
	customitems.addEventListener('mouseenter', (e) => {
		const elemento = e.currentTarget;
		setTimeout(() => {
			customitemss.forEach(customitems => customitems.classList.remove('hover'));
			elemento.classList.add('hover');
		}, 300);
	});
});

if (fila) {
	fila.addEventListener('mouseleave', () => {
		customitemss.forEach(customitems => customitems.classList.remove('hover'));
	});
}