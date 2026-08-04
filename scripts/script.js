
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

function imagesAppending(imageElement) {
  let imageSrc = '';
  let smthWasSet = false;

  const contentImages = document.getElementsByClassName("tutorial-sticky-image-content")
  for (let contentImageElement of contentImages) {

    const rect = contentImageElement.getBoundingClientRect();
    if (300 > rect.top) {
      imageSrc = contentImageElement.src;
      smthWasSet = true;
      console.log(rect.top, "changing image to", imageSrc)
      if (imageElement) {
        imageElement.src = imageSrc;
        imageElement.style.display="block";
      }
    }
  }
  if (!smthWasSet) {
    console.log("no image was chosen. Hid the image");
    imageElement.style.display="none";
  }
}

// ADDS IMAGING SCROLL TO TUTORIALS
window.addEventListener('scroll', function() {
  let containerElement = document.querySelector('.side-container');

  if (containerElement) {
    const imageElement = containerElement.querySelector('img');
    imagesAppending(imageElement);
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
      imagesAppending(tutorialStickyImageElement.querySelector('img'));
    }

});