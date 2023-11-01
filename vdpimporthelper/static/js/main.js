document.querySelector('.sidebar').addEventListener('mouseenter', function (e) {
  this.classList.add('expand');
});

document.querySelector('.sidebar').addEventListener('mouseleave', function (e) {
  this.classList.remove('expand');
});

document.querySelector('.main-panel').addEventListener('mouseenter', function (e) {
  e.target.previousElementSibling.classList.remove('expand');
});

// Nav Profile Image
const profileLogo = document.querySelector('.profile-logo');
const profileMenu = document.querySelector('.profile-menu');
const menuExtender = document.querySelector('.profile-menu-extender');

const targetElements = [profileLogo, profileMenu, menuExtender];

const mouseEvents = {
  mouseover: 'add',
  mouseout: 'remove',
  click: 'add',
};

targetElements.forEach((el) => {
  Object.entries(mouseEvents).forEach(([event, action]) => {
    el.addEventListener(`${event}`, function (e) {
      profileMenu.classList[action]('show');
    });
  });
});
