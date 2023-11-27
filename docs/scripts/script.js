const imageSources = [
  { start: 0, image: 1 },
  { start: 500, image: 2 },
  { start: 1000, image: 3 },
  { start: 1500, image: 4 },
  { start: 2000, image: 1 },
  { start: 2500, image: 5 },
  { start: 3000, image: 6 },
  { start: 3500, image: 1 },
  { start: 4000, image: 7 },
  { start: 4500, image: 8 },
  { start: 5995, image: 9 },
  { start: 6136, image: 10 },
  { start: 6290, image: 11 },
  { start: 6440, image: 12 },
  { start: 6719, image: 13 },
  { start: 6880, image: 14 },
];

// ADDS IMAGING SCROLL TO TUTORIALS
window.addEventListener('scroll', function() {
  const benchmarkElement = document.querySelector('#hands-on-tutorial-for-bechmark-committee');
  const dataElement = document.querySelector('#hands-on-tutorial-for-data-owners');
  const modelElement = document.querySelector('#hands-on-tutorial-for-model-owners');

  const containerElement = document.createElement('div');
  containerElement.classList.add('side-container');

  const imageElement = document.createElement('img');
  imageElement.src = '';
  imageElement.alt = '';

  imageElement.setAttribute('class', 'tutorial-image');
  imageElement.setAttribute('id', 'tutorial-image-1');

  containerElement.appendChild(imageElement);

  if (benchmarkElement) benchmarkElement.appendChild(containerElement);
  else if (dataElement) dataElement.appendChild(containerElement);
  else if (modelElement) modelElement.appendChild(containerElement);

  const sideContainer = document.querySelector('.side-container');
  let image

  if (sideContainer) image = sideContainer.querySelector('img');

  const scrollPosition = window.scrollY;
  let imageSrc = '';
  imageSources.forEach(({ start, image }) => {
    if (scrollPosition > start) {
      imageSrc = `https://raw.githubusercontent.com/gabrielraeder/website/main/docs/static/images/workflow/miccai-tutorial${image}.png`;
    }
  })
  if (image) {
    image.src = imageSrc;
  }
});

// ADDS HOME BUTTON TO HEADER
document.addEventListener('DOMContentLoaded', function() {
  const headerTitle = document.querySelector(".md-header__ellipsis");

  if (headerTitle && window.location.pathname !== "/") {
    const newElement = document.createElement("a");
    newElement.textContent = "Home";
    newElement.classList.add('header_home_btn');
    newElement.href = "/";

    headerTitle.appendChild(newElement);
    console.log(document.querySelector(".header_home_btn"))
    
  }
});