// The element with the id='key_data' holds the selected key's data in its dataset:
//      dataset.name -> path of key
//      dataset.value -> name of selected value
//      dataset.type -> type of selected value
//      dataset.search -> last searched string

// Global variables
const main_keys = {
    0: 'HKEY_CLASSES_ROOT',
    1: 'HKEY_CURRENT_USER',
    2: 'HKEY_LOCAL_MACHINE',
    3: 'HKEY_CURRENT_USER',
    4: 'HKEY_CURRENT_CONFIG'
}

// Resize
// Changes the dimension of the 2 panels
let handler = document.querySelector('.handler');
let wrapper = handler.closest('.container');
let sidenavController = wrapper.querySelector('#sidenav');
let isHandlerDragging = false;
document.addEventListener('mousedown', function(e) {
    if (e.target === handler) {
        isHandlerDragging = true;
    }
});
document.addEventListener('mousemove', function(e) {
    if (!isHandlerDragging) {
        return false;
    }
    let containerOffsetLeft = wrapper.offsetLeft;
    let pointerRelativeX = e.clientX - containerOffsetLeft;
    let boxAminWidth = 150;
    sidenavController.style.width = (Math.max(boxAminWidth, pointerRelativeX - 8)) + 'px';
    sidenavController.style.flexGrow = '0';
});
document.addEventListener('mouseup', function() {
    isHandlerDragging = false;
});

// Main panel
// Selects row from value table on click and updates key_data
$('tbody').on('click', 'tr', function() {
    let key_data = document.getElementById('key_data');
    key_data.dataset.value = this.id;
    key_data.dataset.type = this.dataset.type;
    $(this).toggleClass('selected').siblings('.selected').removeClass('selected');
    let value_buttons = document.querySelectorAll('.value_dependent');
    for(let button in value_buttons) {
        value_buttons[button].disabled = false;
    }
});

// Selects row from value table
function select_value(id) {
    let key_data = document.getElementById('key_data');
    let rows = Array.from(document.getElementById('selected_key').querySelectorAll('.table_row'));
    for(let row in rows) {
        if(id === rows[row].id) {
            key_data.dataset.value = rows[row].id;
            key_data.dataset.type = rows[row].dataset.type;
            $(rows[row]).toggleClass('selected').siblings('.selected').removeClass('selected');
            let value_buttons = document.querySelectorAll('.value_dependent');
            for(let button in value_buttons) {
                value_buttons[button].disabled = false;
            }
            return;
        }
    }
}

// Selects key from side panel, updates key_data and calls function to update the values table
function select_key(id, value='') {
    let key_data = document.getElementById('key_data');
    let key_buttons = document.querySelectorAll('.key_dependent');
    key_data.textContent = main_keys[id[0]] + id.slice(1);
    key_data.dataset.name = id;
    key_data.dataset.value = '';
    key_data.dataset.type = '';
    for(let button in key_buttons) {
        key_buttons[button].disabled = false;
    }
    let value_buttons = document.querySelectorAll('.value_dependent');
    for(let button in value_buttons) {
        value_buttons[button].disabled = true;
    }
    $.getJSON('/inspect_key/' + encodeURIComponent(id), function (result) {
        list_values(result);
        if(value) {
            select_value(value);
        }
    });
}

// Updates the values table
function list_values(values) {
    let old_tr = document.getElementById('selected_key');
    let child = old_tr.lastElementChild;
    while(child) {
        child.remove();
        child = old_tr.lastElementChild;
    }
    for(let value in values) {
        const tr = document.createElement('tr');
        tr.id = values[value][0];
        tr.dataset.type = values[value][2];
        tr.className = 'table_row';
        const td0 = document.createElement('td');
        td0.textContent = values[value][0];
        const td1 = document.createElement('td');
        td1.textContent = values[value][2];
        const td2 = document.createElement('td');
        td2.textContent = values[value][1];
        tr.appendChild(td0);
        tr.appendChild(td1);
        tr.appendChild(td2);
        old_tr.appendChild(tr)
    }
}

// Creates new key and updates the key tree
function new_key() {
    let id = document.getElementById('key_data').dataset.name;
    $.getJSON('/create_key/' + encodeURIComponent(id), function () {
        if(id.slice(-1) !== '\\') {
            id += '\\';
        }
        update_branch(id, true);
    });
}

// Creates new value and updates the values table
function new_value() {
    let type = prompt('Enter value type (0 -> REG_SZ, 1 -> REG_MULTI_SZ, 2 -> REG_EXPAND, 3 -> REG_DWORD');
    let id = document.getElementById('key_data').dataset.name;
    let param = id + '\\\\param1\\\\' + type;
    if(0 <= type && type <= 3) {
        $.getJSON('/create_value/' + encodeURIComponent(param), function () {
            select_key(id);
        });
    } else {
        window.alert('Invalid type');
    }
}

// Renames selected key
function rename_key() {
    let id = document.getElementById('key_data').dataset.name;
    if(id.length < 3) {
        window.alert('Can not rename base key');
        return;
    }
    let base_name = id.split('\\');
    base_name.pop();
    base_name = base_name.join('\\');
    let new_name = prompt('New name');
    if(new_name.includes('\\') || !new_name) {
        return;
    }
    let check_name = base_name + '\\' + new_name;
    if(valid_key_name(check_name)) {
        check_name = id + '\\\\param1\\\\' + new_name;
        $.getJSON('/rename_key/' + encodeURIComponent(check_name), function (result) {
            if(result === '[RENAME_KEY]: Invalid key name') {
                window.alert('Key name not valid')
            }
            base_name = base_name + '\\';
            update_branch(base_name, false);
            select_key(base_name + new_name);
        });
    } else {
        window.alert('Key name not valid')
    }
}

// Deletes selected key and all of its sub keys
function delete_key() {
    let id = document.getElementById('key_data').dataset.name;
    if(id.length > 2) {
        $.getJSON('/delete_key/' + encodeURIComponent(id), function () {
            id = id.slice(0, id.lastIndexOf('\\'));
            update_branch(id + '\\', false);
            select_key(id);
        });
    } else {
        window.alert('Can not delete main keys');
    }
}

// Renames selected value
function rename_value() {
    let key_data = document.getElementById('key_data');
    let id = key_data.dataset.name;
    let new_name = prompt('Enter value name')
    if(!new_name) {
        return;
    }
    if(valid_value_name(new_name)) {
        let param = id + '\\\\param1\\\\' + key_data.dataset.value + '\\\\param2\\\\' + new_name;
        $.getJSON('/rename_value/' + encodeURIComponent(param), function () {
            select_key(id);
        });
    } else {
        window.alert('Invalid name, cannot have more values with the same name')
    }
}

// Changes data of selected value
function edit_value() {
    let key_data = document.getElementById('key_data');
    let id = key_data.dataset.name;
    let new_value;
    if(key_data.dataset.type === 'REG_MULTI_SZ') {
        new_value = prompt('Enter strings - use "[\\end]" as delimiter');
    } else {
        new_value = prompt('Enter new value');
    }
    if(valid_value_content(key_data.dataset.type, new_value)) {
        let param = id + '\\\\param1\\\\' + key_data.dataset.value + '\\\\param2\\\\' + new_value;
        $.getJSON('/edit_value/' + encodeURIComponent(param), function () {
            // update_branch(id + '\\', false);
            select_key(id);
        });
    } else {
        window.alert('Invalid value');
    }
}

// Deletes selected value
function delete_value() {
    let key_data = document.getElementById('key_data');
    let string = key_data.dataset.name + '\\\\param1\\\\' + key_data.dataset.value;
    $.getJSON('/delete_value/' + encodeURIComponent(string), function () {
        update_table();
    });
}

// Reads string from user input and searches for first occurrence
function find_string() {
    let key_data = document.getElementById('key_data');
    let search_string = prompt('Search for string');
    if(!valid_string(search_string)) {
        return;
    }
    key_data.dataset.search = search_string;
    find_next_string();
}

// Searches for next occurrences of last string
function find_next_string() {
    let key_data = document.getElementById('key_data');
    let search_string = key_data.dataset.search;
    search_string = key_data.dataset.name + '\\\\param1\\\\' + key_data.dataset.value + '\\\\param2\\\\' + search_string;
    $.getJSON('/find_string/' + encodeURIComponent(search_string), function (result) {
        if(result.length) {
            search_result(result);
        } else {
            window.alert('Finished searching through registry');
        }
    });
}

// Selects resulted key and resulted value
function search_result(search_value) {
    let path = search_value.substring(0, search_value.lastIndexOf('\\\\value\\\\'));
    let value = search_value.substring(search_value.lastIndexOf('\\\\value\\\\') + 9);
    let path_array = path.split('\\');
    let expand_path = path_array.shift();
    expand_all(expand_path, path_array, path, value);
}

// Expands all nodes included in the received path, then selects a key and a value
function expand_all(expand_path, path_array, key, value) {
    if(path_array.length) {
        expand_path += '\\';
        console.log(expand_path);
        let checkbox = document.getElementById(expand_path);
        console.log(checkbox);
        if(checkbox.checked === true) {
            remove_branch(expand_path);
        }
        $.getJSON('/expand_key/' + encodeURIComponent(expand_path), function (result) {
            add_elem(result, expand_path);
            expand_path = expand_path + path_array.shift();
            expand_all(expand_path, path_array, key, value);
        });
    } else {
        select_key(expand_path, value);
    }
}

function valid_string(string) {
    return string !== '\\\\param1\\\\' && string !== '\\\\param2\\\\';
}

// Returns false if there are duplicates or the name contains a backslash
function valid_key_name(name) {
    if(!valid_string(name)) {
        return false;
    }
    let parent_name = name.split('\\');
    parent_name.pop();
    parent_name = parent_name.join('\\') + '\\';
    let children = document.getElementById(parent_name + '\\sub').querySelectorAll('.child');
    name += '\\';
    for(let child in children) {
        if(children[child].id.toLowerCase() === name.toLowerCase()) {
            return false;
        }
    }
    return true;
}

// Returns false if there are duplicates
function valid_value_name(new_value) {
    if(!valid_string(new_value)) {
        return false;
    }
    let rows = Array.from(document.getElementById('selected_key').querySelectorAll('.table_row'));
    for(let row in rows) {
        if(new_value === rows[row].id) {
            return false;
        }
    }
    return true;
}

// Validates data from user input, depending on value type
function valid_value_content(type, new_value) {
    if(!valid_string(new_value)) {
        return false;
    }
    if(type === 'REG_DWORD') {
        return new_value >= 0 && new_value <= 4294967295;
    }
    return true;
}

// Removes from value table selected entry and selects the default value
function update_table() {
    let key_data = document.getElementById('key_data');
    let value = key_data.dataset.value;
    value = document.getElementById(value);
    value.remove();
    value = document.getElementById('(default)');
    $(value).toggleClass('selected').siblings('.selected').removeClass('selected');
    key_data.dataset.value = '(default)';
}

// Refreshes branch from the tree view and adds visible checkbox if 'leaf' node receives a sub key
function update_branch(id, new_value) {
    let checkbox = document.getElementById(id);
    if(new_value) {
        checkbox.style.visibility = 'visible';
    }
    if(checkbox.checked === true) {
        remove_branch(id);
        expand_branch(id);
    }
}

// Tree view checkbox functions
// Hides main keys
function computer() {
    let checkbox = document.getElementById('Computer');
    let main_keys = document.getElementById('main_keys');
    if(checkbox.checked === true) {
        main_keys.style.visibility='visible';
    } else {
        main_keys.style.visibility='hidden';
    }
}

function checkbox(id) {
    let checkbox = document.getElementById(id);
    if(checkbox.checked === true) {
        expand_branch(id);
    } else {
        remove_branch(id);
    }
}

function expand_branch(id) {
    $.getJSON('/expand_key/' + encodeURIComponent(id), function (result) {
        add_elem(result, id);
    });
}

function add_elem(result, id) {
    const checkbox = document.getElementById(id);
    if(checkbox.checked === false) {
        checkbox.checked = true;
    }
    const div = document.createElement('div');
    div.id = id + '\\sub';
    const ul = document.createElement('ul');
    ul.it = id + '\\sub_ul';
    for(let sub_key in result) {
        ul.appendChild(update_tree(id, result[sub_key]));
    }
    div.appendChild(ul);
    const parent = document.getElementById(id + '\\\\_label');
    parent.insertAdjacentElement('afterend', div);
}

function update_tree(id, sub_key) {
    let li = document.createElement('li');
    let input = document.createElement('input');
    input.type = 'checkbox';
    input.id = id + sub_key[1] + '\\';
    input.className = 'child';
    input.checked = false;
    if(sub_key[0] === '0') {
        input.style.visibility = 'hidden';
    }
    input.addEventListener('click', function () {
        return checkbox(input.id);
    }, false);
    let label = document.createElement('label');
    label.htmlFor = input.id;
    let a = document.createElement('a');
    a.id = input.id + '\\\\_label';
    a.textContent = ' 📁 ' + sub_key[1];
    a.href = '#';
    a.addEventListener('click', function () {
        return select_key(id + sub_key[1]);
    }, false);
    label.appendChild(a)
    li.appendChild(input);
    li.appendChild(label);
    return li;
}

function remove_branch(id) {
    const elem = document.getElementById(id + '\\sub');
    elem.remove();
}