/*
 * CONSTANTS
 */
const DAYS_MAP = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
const ALL_PEOPLE = ["rick", "youri", "robert", "milan", "dag"];
const DAY_STATES = [ "E", "X", "O", "?" ];

let userWebSocket = new WebSocket("ws://172.104.143.161/ws");
//let userWebSocket = new WebSocket("ws://127.0.0.1:8000/ws");

function get_correct_socket() {
	try {
		return new WebSocket("ws://127.0.0.1:8000/ws");
	} catch (error) {
		console.log(error);
		console.log("Connecting to sis50.nl server");
		return new WebSocket("ws://172.104.143.161/ws");
	}
}

const DOM_BODY = document.getElementsByTagName("body")[0];

/*
 * LOCAL FUNCTIONS
 */
function set_reset_background(url) {

	console.log(`Setting Background Image: ${url}`);

	if (url !== "") {
		DOM_BODY.style.backgroundImage = `url(${url})`;
		DOM_BODY.style.backgroundSize = "cover";
		localStorage.setItem("background-url", `${url}`);
	} else {
		DOM_BODY.style.backgroundColor = "#101010";
		DOM_BODY.style.backgroundImage = '';
		localStorage.setItem("background-url", "");
	}
}


function change_background_image(event) {

	var newBackgroundUrl = document.getElementById("new_background").value;
	set_reset_background(newBackgroundUrl);
	event.preventDefault();
}


function new_model_item(itemCount, itemName) {
	return `<div>
		<p id="text-${itemCount}">${itemName}</p>
		<button class="editItemButton" id="${itemCount}e" onclick="editItem(this.id)">Editen</button>
		<button class="removeButton" id="${itemCount}" onclick="removeItemMessage(this.id)">X</button>
		</div>`;
}


function highlight_todays_row() {

	var currentDate = new Date();
	var today = DAYS_MAP[currentDate.getDay()]

	for (var i = 0; i < ALL_PEOPLE.length; i++) {

		var selectedPerson = `${ALL_PEOPLE[i]}-${today}`
		var selectedElement = document.getElementById(selectedPerson);
		selectedElement.style.backgroundColor = '#0a3b0a90';

		console.log(`Changed for Highlight Today: ${selectedPerson}`);
	}
}


/*
 * DATA FORMAT
 * [event]^[itemId]^[newValue]
 */

/*
 * WEBSOCKET HANDLING
 */
userWebSocket.onmessage = function(event) {

	var itemList = document.getElementById("item_list");

	// unpacking the message received
	var message = event.data.split("^");

	var messageType = message[0];
	var mEffectedItem = message[1];
	var mNewValue = message[2];

	console.log(message);

	if (messageType == "addItem") {
		var newListItem = document.createElement("li")
		newListItem.setAttribute("id", `list_item-${mEffectedItem}`)
		newListItem.innerHTML = new_model_item(mEffectedItem, mNewValue);

		itemList.appendChild(newListItem);
	} else if (messageType == "deleteItem") {
		document.getElementById(mEffectedItem).remove();
		
	} else if (messageType == "changeDay") {
		if (mNewValue === "E") {
			mNewValue = "<space></space>";
		}
		document.getElementById(mEffectedItem).innerHTML = mNewValue;
	} else if (messageType == "editItem") {
		document.getElementById(`text-${mEffectedItem}`).innerHTML = mNewValue;
	} else if (messageType == "addNotice") {
		var newChatItem = document.createElement("p")
		var chatList = document.getElementById("chatList");

		console.log(chatList.children.length);
		if (chatList.children.length >= 4) {
			console.log("removing child")
			chatList.removeChild(chatList.lastChild);
		}

		newChatItem.innerHTML = mNewValue;

		console.log(message);

		chatList.prepend(newChatItem);
	} else if (messageType == "changeComic") {
		document.getElementById("randomComicImg").src = mNewValue;
		console.log(`Got image: ${mNewValue}`);
	} else if (messageType == "changeImageTitle") {
		document.getElementById("randomComicImg").title = mNewValue;
		console.log(`Changed Image title to : ${mNewValue}`);
	} else if (messageType == "changeComicHref") {
		document.getElementById("randomComicLink").href = mNewValue;
		console.log(`Changed Image href to : ${mNewValue}`);
	}
};

function editItem(itemId) {
	var itemToEditId = itemId.slice(0, -1) // cut off last character which is e
	var toChangeElement = document.getElementById(`text-${itemToEditId}`);
	var newItemName = prompt("Edit Item", `${toChangeElement.innerHTML}`);

	userWebSocket.send(`editItem^${itemToEditId}^${newItemName}`)
}

function removeItemMessage(itemId) {
	var itemValue = document.getElementById(`text-${itemId}`).innerHTML;
	userWebSocket.send(`deleteItem^list_item-${itemId}^${itemValue}`)
	console.log(`deleteItem^list_item-${itemId}^${itemValue}`);
}

function addItemMessage(event) {
	var newItem = document.getElementById("add_item_field");
	if (!(newItem.value === "")) {
		userWebSocket.send(`addItem^_^${newItem.value}`);
		console.log(`addItem^_^${newItem.value}`)
	}
	newItem.value="";
	event.preventDefault();
}

function changeDayStatus(itemId) {
	var current_day = document.getElementById(itemId);
	var current_day_state = current_day.innerHTML;
	if (current_day_state === "<space></space>") {
		current_day_state = 'E'
	}
	var new_index = (DAY_STATES.indexOf(current_day_state) + 1) % DAY_STATES.length;
	userWebSocket.send(`changeDay^${itemId}^${DAY_STATES[new_index]}`);
	console.log(`changeDay^${itemId}^${DAY_STATES[new_index]}`)
}

function addNotice(event) {
	
	var newNoticeTextItem = document.getElementById("newNoticeText");
	console.log(newNoticeTextItem)
	userWebSocket.send(`addNotice^_^${newNoticeTextItem.value}`)

	newNoticeTextItem.value = "";

	event.preventDefault()
}

/*
 * EXECUTION
 */

// Establishing websocket connection and retrieving state.
// retrieves the most up-to-date for the given user, !!NOT BROADCAST!!
// will be received as fragments of all possible operations, instead of as one big string
userWebSocket.onopen = function() {
	 userWebSocket.send("retrieveState^_^_") 
};

// Setting background image if previously saved.
try {

	var savedBackgroundUrl = localStorage.getItem("background-url");
	set_reset_background(savedBackgroundUrl);
	
} catch (error) {

	console.log(`No Previous Background Image: ${error}`);
	lcoalStorage.setItem("background-url", "");
}

highlight_todays_row();


