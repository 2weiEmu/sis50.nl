# The Sis50 site for groceries, and cooking schedules

This site will have basically functionality that includes being able to change the cooking timetable and add things to the shopping list.

The initial version is not going to include password authentication, though this will be added later so that people actually from Sis50 only can change the relevant notices.

The layout of the site will be as follows:

Table for the date of cooking:

| Rick | Youri | Robert | Milan | Dag |
|:----:|:-----:|:------:|:-----:|:---:|
| X    | X     | O      |       | Man |
| X    |       |        |       | Din |
| X    | X     | O      | X     | Woe |
| X    |       | O      |       | Man |
| X    | O     |        | X     | Don |
| X    |       | O      | X     | Vri |
| X    |       | O      | X     | Zat |
| ?    | O     |        | X     | Zon |

as an example table... the current day will be highlighted

There will also be a simple shopping list

<style>

    li {
        display: flex;
    }
    #inner_item {
        display: flex;
        margin: 0;
        padding: 10px;

        background-color: #f0f0f0;
    }

    #inner_item p {
        justify-content: space-evenly;
    }

    span {
        display: inline-block;
        width: 50px;
    }
</style>

<body>
    <ul>
        <li><div id="inner_item">item 1<span></span><button>X</button></div></li>
        <li><div id="inner_item">item 2<span></span><button>X</button></div></li>
        <li><div id="inner_item">item 3<span></span><button>X</button></div></li>
        <li><div id="inner_item">item 4<span></span><button>X</button></div></li>
        <li><div id="inner_item">item 5<span></span><button>X</button></div></li>
    </ul>
</body>
