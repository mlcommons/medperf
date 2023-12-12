const tutorials = {
  benchmark: [
    { image: 1, content:'overview' },
    { image: 2, content:'Before You Start' },
    { image: 3, content:'1. Implement a Valid Workflow' },
    // { image: 4, content:'' },
    // { image: 1, content:'' },
    // { image: 5, content:'' },
    // { image: 6, content:'' },
  ],
  model: [
    { image: 1, content:'overview' },
    { image: 2, content:'Before You Start' },
    { image: 3, content:'1. Test your MLCube Compatibility' },
    // { image: 4, content:'' },
    // { image: 1, content:'' },
    // { image: 5, content:'' },
    // { image: 6, content:'' },
  ],
  data: [
    { image: 1, content:'overview' },
    { image: 2, content:'Before You Start' },
    { image: 3, content:'1. Prepare your Data' },
    // { image: 4, content:'' },
    // { image: 1, content:'' },
    // { image: 5, content:'' },
    // { image: 6, content:'' },
  ],
};

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

function imagesAppending(elements, imageElement, tutorial) {
  let imageSrc = '';

  tutorials[tutorial].forEach(({ image, content }) => {
    let targetElement;

    for (const element of elements) {
      if (element.innerHTML.includes(content)) {
        targetElement = element;
        break;
      }
    }

    const rect = targetElement.getBoundingClientRect();
    if (120 > rect.top) {
      imageSrc = `https://raw.githubusercontent.com/gabrielraeder/website/main/docs/static/images/workflow/miccai-tutorial${image}.png`;
      if (imageElement) {
        imageElement.src = imageSrc;
      }
    }
    // TODO: add a default image instead (or hide the whole image elem if possible)
    else if (rect.top > 120 && content === 'overview') {
      imageElement.src = '';
    }
  })
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

    const tutorialStickyImageElement = createSideImageContainer();

    // TODO: here is bug, I add element on all the pages, not only on the tutorials
    const contentElement = document.getElementsByClassName('md-main__inner')[0];
    contentElement.appendChild(tutorialStickyImageElement);

});