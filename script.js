const statsElement = document.getElementById('stats-sentence');
const startTimeElement = document.getElementById('start-time');
const gaugePercentageElement = document.getElementById('gauge-percentage');
const gaugeTextElement = document.getElementById('gauge-text');

const socket = new WebSocket('ws://localhost:8080/ws');

socket.onopen = function (event) {
  console.log('WebSocket connection established');
};

socket.onmessage = function (event) {
  try {
    const data = JSON.parse(event.data);
    const totalImages = data.images_with_alt + data.images_without_alt;

    // Update the stats sentence with formatted numbers
    statsElement.innerHTML = `Out of ${formatNumber(totalImages)} observed images, <strong>${formatNumber(data.images_without_alt)}</strong> are missing alt text.`;

    // Calculate and update the percentage of images missing alt text
    const haveAltPercentage = totalImages > 0
      ? ((data.images_with_alt / totalImages) * 100).toFixed(1)
      : 0;

    // Update the gauge
    updateGauge(haveAltPercentage);

    if (data.start_time) {
      const startDate = new Date(data.start_time);
      startTimeElement.textContent = `Tracking started on: ${startDate.toLocaleString()}`;
    }
  } catch (error) {
    console.error('Error parsing WebSocket message:', error);
  }
};

socket.onclose = function (event) {
  console.log('WebSocket connection closed:', event);
};

socket.onerror = function (error) {
  console.error('WebSocket error:', error);
};

function updateGauge(percentage) {
  const gaugeElement = document.querySelector('.semi-circle--mask');
  const needleElement = document.querySelector('.needle');
  const rotation = (percentage / 100) * 180;
  gaugeElement.style.transform = `rotate(${rotation}deg) translate3d(0, 0, 0)`;
  needleElement.style.transform = `rotate(${rotation}deg)`;
  gaugePercentageElement.textContent = percentage <= 90 ? `Only ${percentage}%` : `${percentage}%`;
  gaugeTextElement.textContent = "of images have alt text!";
}

// Helper function to format numbers with commas
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
