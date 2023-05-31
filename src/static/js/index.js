
// CONSTANT STATE
var days_map = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
var all_people = ["rick", "youri", "robert", "milan", "dag"]
var day_states = [ "<space></space>", "X", "O", "?" ];

// make sure this connects to the correct server
//var ws = new WebSocket("ws://172.104.143.161/ws")
var ws = new WebSocket("ws://127.0.0.1:8000/ws")

// CLIENT SIDE FUNCTIONS
function changeBackgroundImage(event) {

	var new_background_url = document.getElementById("new_background").value;
	var body = document.getElementsByTagName("body")[0];

	var table = document.getElementsByTagName("table")[0];
	var buy_list = document.getElementById("buy_list");

	if (new_background_url != "") {
		body.style.backgroundImage = `url(${new_background_url})`;
		body.style.backgroundSize = "cover";

		table.style.backgroundColor = "#ffffff0f"
		buy_list.style.backgroundColor = "#ffffff0f"
		localStorage.setItem("background-url", `${new_background_url}`)

	} else {
		body.style.background = "linear-gradient(to bottom right, #000000, #1f1f1f)";
		buy_list.style.backgroundColor = "#00000000";
		table.style.backgroundColor = "#00000000";
		localStorage.setItem("background-url", "")
	}

	event.preventDefault();
}


// changing saved background image

try {
	var backgroundUrl = localStorage.getItem("background-url");
	console.log(`background: ${backgroundUrl}`)
	if (backgroundUrl != "") {

	var body = document.getElementsByTagName("body")[0];

	var table = document.getElementsByTagName("table")[0];
	var buy_list = document.getElementById("buy_list");
		body.style.backgroundImage = `url(${backgroundUrl})`;
		body.style.backgroundSize = "cover";

		table.style.backgroundColor = "#ffffff0f"
		buy_list.style.backgroundColor = "#ffffff0f"
		localStorage.setItem("background-url", `${backgroundUrl}`)
		console.log("read and changed");
	}
} catch (error) {
	console.log(error)
	body.style.background = "linear-gradient(to bottom right, #000000, #1f1f1f)";
	buy_list.style.backgroundColor = "#00000000";
	table.style.backgroundColor = "#00000000";
	localStorage.setItem("background-url", "")
}

function newModelItem(itemCount, itemName) {
	return `<div>
		<p id="text-${itemCount}">${itemName}</p>
		<button class="editItemButton" id="${itemCount}e" onclick="editItem(this.id)">Editen</button>
		<button class="removeButton" id="${itemCount}" onclick="removeItemMessage(this.id)">X</button>
		</div>`
}


function highlightCurrentDayRow() {

	var current_date = new Date();
	var today = days_map[current_date.getDay()]

	for (var i = 0; i < all_people.length; i++) {
		var select_person = `${all_people[i]}-${today}`
		var select_element = document.getElementById(select_person);
		console.log(`changed ${select_person}`);
		select_element.style.backgroundColor = '#0a3b0a90';
		console.log('selection complete...');
	}
}
highlightCurrentDayRow();


/**
 * DATA FORMAT
 * [event]^[itemId]^[newValue]
**/

// SERVER INTERACTION FUNCTIONS
ws.onmessage = function(event) {

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
		newListItem.innerHTML = newModelItem(mEffectedItem, mNewValue);

		itemList.appendChild(newListItem);
	} else if (messageType == "deleteItem") {
		document.getElementById(mEffectedItem).remove();
		
	} else if (messageType == "changeDay") {
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
	}
};

function editItem(itemId) {
	var itemToEditId = itemId.slice(0, -1) // cut off last character which is e
	var toChangeElement = document.getElementById(`text-${itemToEditId}`);
	var newItemName = prompt("Edit Item", `${toChangeElement.innerHTML}`);

	ws.send(`editItem^${itemToEditId}^${newItemName}`)
}

function removeItemMessage(itemId) {
	var itemValue = document.getElementById(`text-${itemId}`).innerHTML;
	ws.send(`deleteItem^list_item-${itemId}^${itemValue}`)
	console.log(`deleteItem^list_item-${itemId}^${itemValue}`);
}

function addItemMessage(event) {
	var newItem = document.getElementById("add_item_field");
	if (!(newItem.value === "")) {
		ws.send(`addItem^_^${newItem.value}`);
		console.log(`addItem^_^${newItem.value}`)
	}
	newItem.value="";
	event.preventDefault();
}

function changeDayStatus(itemId) {
	var current_day = document.getElementById(itemId);
	var current_day_state = current_day.innerHTML;
	var new_index = (day_states.indexOf(current_day_state) + 1) % day_states.length;
	ws.send(`changeDay^${itemId}^${day_states[new_index]}`);
	console.log(`changeDay^${itemId}^${day_states[new_index]}`)
}

function addNotice(event) {
	
	var newNoticeTextItem = document.getElementById("newNoticeText");
	console.log(newNoticeTextItem)
	ws.send(`addNotice^_^${newNoticeTextItem.value}`)

	newNoticeTextItem.value = "";

	event.preventDefault()

}

ws.onopen = function() {
	 ws.send("retrieveState^_^_") 
};
// retrieves the most up-to-date for the given user, !!NOT BROADCAST!!
// will be received as fragments of all possible operations, instead of as one big string

