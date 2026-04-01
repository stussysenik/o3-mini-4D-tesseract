const buttons = Array.from(document.querySelectorAll('[data-device-select]'));
const stages = Array.from(document.querySelectorAll('[data-device-stage]'));

function activateDevice(deviceId) {
  buttons.forEach((button) => {
    button.classList.toggle('is-active', button.dataset.deviceSelect === deviceId);
  });
  stages.forEach((stage) => {
    stage.classList.toggle('is-active', stage.dataset.deviceStage === deviceId);
  });
}

buttons.forEach((button) => {
  button.addEventListener('click', () => activateDevice(button.dataset.deviceSelect));
});
