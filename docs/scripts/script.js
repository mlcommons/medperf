
function createSideImageContainer() {
  const containerElement = document.createElement('div');
  containerElement.classList.add('side-container');

  const imageElement = document.createElement('img');
  imageElement.src = '';
  imageElement.alt = '';

  imageElement.setAttribute('class', 'tutorial-sticky-image');
  imageElement.setAttribute('id', 'tutorial-sticky-image');

  containerElement.appendChild(imageElement);

  return containerElement;
}

function imagesAppending(elements, imageElement) {
  let imageSrc = '';

  const contentImages = document.getElementsByClassName("tutorial-sticky-image-content")
  for (let contentImageElement of contentImages) {

    // TODO: at the very first page load, no src is shown => broken image
    const rect = contentImageElement.getBoundingClientRect();
    if (120 > rect.top) {
      imageSrc = contentImageElement.src;
      console.log(rect.top, "changing image to", imageSrc)
      if (imageElement) {
        imageElement.src = imageSrc;
      }
    }
  }
}

// ADDS IMAGING SCROLL TO TUTORIALS
window.addEventListener('scroll', function() {
  let containerElement = document.querySelector('.side-container');

  if (containerElement) {
    const imageElement = containerElement.querySelector('img');
    const elements = document.querySelectorAll('h2');
    const currentTutorial = window.location.href.includes('benchmark') ? 'benchmark' : window.location.href.includes('model') ? 'model' : 'data';
    imagesAppending(elements, imageElement, currentTutorial);
  }
})

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

    const contentImages = document.getElementsByClassName("tutorial-sticky-image-content");
    if (contentImages.length) {
      console.log('content images found: ', contentImages)
      // we add an element only if there are content images on this page to be shown
      const tutorialStickyImageElement = createSideImageContainer();
      const contentElement = document.getElementsByClassName('md-content')[0];
      contentElement.parentNode.insertBefore(tutorialStickyImageElement, contentElement.nextSibling);
    }

});