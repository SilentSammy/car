// Limits and directions
let throttleDirection = 0;
let throttleLimit = 0.5;
let steeringDirection = 0;
let steeringLimit = 0.5;

// Previous state values
let prevThrottle = 0;
let prevSteering = 0;

// Browser data
const isLocalDocument = window.location.protocol === 'file:' || window.location.protocol === 'content:';
const isMobile = navigator.userAgentData.mobile;

// Request variables
let isRequestInProgress = false;

function sendUpdate() {
    function roundToMultiple(value, multiple) {
        return Math.round(value / multiple) * multiple;
    }
    
    // Calculate the state values and round them to the nearest 0.05
    let throttle = Number(roundToMultiple(throttleDirection * throttleLimit, 0.05).toFixed(2));
    let steering = Number(roundToMultiple(steeringDirection * steeringLimit, 0.05).toFixed(2));

    // If there was no change, or a request is already in progress, do nothing
    if ((throttle === prevThrottle && steering === prevSteering) || isRequestInProgress) {
        console.log('No change or request in progress');
        return;
    }
    else {
        // We start a new request
        isRequestInProgress = true;

        // Determine which values changed, and append them to params
        let params = new URLSearchParams();
        if (steering !== prevSteering) {
            params.append('s', steering);
        }
        if (throttle !== prevThrottle) {
            params.append('t', throttle);
        }
        
        // Print the parameters to the console, as JSON
        console.log(JSON.stringify(Object.fromEntries(params.entries())));

        // Save the current state values
        prevThrottle = throttle;
        prevSteering = steering;
        
        // Determine URL
        let currentUrl;
        if (isLocalDocument) { // If local file, use user-provided URL
            currentUrl = document.getElementById('urlInput').value;
        } else { // If hosted, use current base URL
            currentUrl = `${window.location.protocol}//${window.location.hostname}`;
            if (window.location.port) {
                currentUrl += `:${window.location.port}`;
            }
        }
        console.log('Current URL:', currentUrl);

        // Assemble and send request
        const requestUrl = `${currentUrl}/?${params.toString()}`;
        fetch(requestUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log(data);
            })
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
            })
            .finally(() => {
                isRequestInProgress = false;
                sendUpdate();
            });
    }
}

function updateThrottleLimit() {
    const throttleLimitSlider = document.getElementById('throttleSlider');
    const throttleLimitLabel = document.getElementById('throttleLimit');
    let value = throttleLimitSlider.value;

    // Pad the value with non-breaking spaces to ensure it is always 3 characters long
    value = value.padStart(3, ' ').replace(/ /g, '\u00A0') + "%";
    throttleLimitLabel.innerText = value;

    // Update the throttle limit
    throttleLimit = throttleLimitSlider.value / 100;
}
function updateSteeringLimit() {
    const steeringLimitSlider = document.getElementById('steeringSlider');
    const steeringLimitLabel = document.getElementById('steeringLimit');
    let value = steeringLimitSlider.value;

    // Pad the value with non-breaking spaces to ensure it is always 3 characters long
    value = value.padStart(3, ' ').replace(/ /g, '\u00A0') + "%";
    steeringLimitLabel.innerText = value;

    // Update the steering limit
    steeringLimit = steeringLimitSlider.value / 100;
}

function load() {
    // Generic function to propagate click to child radio button
    function propagateClickToRadioButton(event) {
        const radioButton = this.querySelector('input[type="radio"]');
        if (radioButton && event.target !== radioButton) {
            radioButton.click();
        }
    }

    console.log('isMobile:', isMobile);
    console.log('isLocalDocument:', isLocalDocument);
    
    // Add click event listeners to radio containers
    const radioContainers = document.querySelectorAll('.radio-container');
    radioContainers.forEach(container => {
        container.addEventListener('click', propagateClickToRadioButton);
    });

    if (isMobile) {
        document.querySelectorAll('.desktop').forEach(element => element.style.display = 'none');
    } else {
        document.querySelectorAll('.mobile').forEach(element => element.style.display = 'none');
    }
    
    if (isLocalDocument) { // If local file, show settings dialog
        document.getElementById('settingsDialog').showModal();
        document.getElementById('urlInput').value = localStorage.getItem('url');
    }

    function handleKeyEvent(event, isKeyDown) {
        let keyHandled = true;
        switch(event.key) {
            case 'w':
                throttleDirection = isKeyDown ? 1 : 0;
                break;
            case 's':
                throttleDirection = isKeyDown ? -1 : 0;
                break;
            case 'a':
                steeringDirection = isKeyDown ? -1 : 0;
                break;
            case 'd':
                steeringDirection = isKeyDown ? 1 : 0;
                break;
            default:
                keyHandled = false;
        }
        if (keyHandled) {
            sendUpdate();
        }
    }
    
    document.addEventListener('keydown', function(event) {
        handleKeyEvent(event, true);
    });
    
    document.addEventListener('keyup', function(event) {
        handleKeyEvent(event, false);
    });
}

function saveUrl() {
    const urlInput = document.getElementById('urlInput');
    localStorage.setItem('url', urlInput.value);
}

// Function to close the dialog
function closeDialog() {
    document.getElementById('settingsDialog').close();
}