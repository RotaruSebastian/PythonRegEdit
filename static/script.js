main_keys = {
    0: 'HKEY_CLASSES_ROOT',
    1: 'HKEY_CURRENT_USER',
    2: 'HKEY_LOCAL_MACHINE',
    3: 'HKEY_CURRENT_USER',
    4: 'HKEY_CURRENT_CONFIG'
}
// Resize
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
document.addEventListener('mouseup', function(e) {
    isHandlerDragging = false;
});
// Main panel
$('tbody').on('click', 'tr', function(e) {
    $(this)
        .toggleClass('selected')
        .siblings('.selected')
        .removeClass('selected');
    let value_buttons = document.querySelectorAll('.value_dependent');
    for(let button in value_buttons) {
        value_buttons[button].disabled = false;
    }
});
function select_key(id) {
    let h = document.getElementById('key_name');
    let key_buttons = document.querySelectorAll('.key_dependent');
    h.textContent = main_keys[id[0]] + id.slice(1);
    h.dataset.name = id;
    for(let button in key_buttons) {
        key_buttons[button].disabled = false;
    }
    let value_buttons = document.querySelectorAll('.value_dependent');
    for(let button in value_buttons) {
        value_buttons[button].disabled = true;
    }
    $.getJSON('/inspect_key/' + encodeURIComponent(id), function (result) {
        list_values(result);
    });
}
function list_values(values) {
    let old_tr = document.querySelectorAll('#new_key');
    $(old_tr).remove();
    old_tr = document.getElementById('selected_key');
    for(let value in values) {
        const tr = document.createElement('tr');
        tr.id = 'new_key';
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
function new_key() {
    let id = document.getElementById('key_name');
    id = id.dataset.name;
    console.log(id);
    $.getJSON('/create_key/' + encodeURIComponent(id), function () {
        update_branch(id + '\\');
    });
}
function new_value() {
    // chestii prompt
}
function rename_key() {
    // savekey + loadkey
}
function delete_key() {
    let id = document.getElementById('key_name');
    id = id.dataset.name;
    if(id.length > 2) {
        $.getJSON('/delete_key/' + encodeURIComponent(id), function () {
            id = id.slice(0, id.lastIndexOf('\\'));
            update_branch(id + '\\');
            select_key(id);
        });
    } else {
        window.alert('Can not delete main keys');
    }
}
function find_string() {

}
function rename_value() {
    // chestii prompt
}
function edit_value() {
    // chestii prompt
}
function delete_value() {

}
function update_branch(id) {
    let checkbox = document.getElementById(id);
    if(checkbox.checked === true) {
        remove_branch(id);
        expand_branch(id);
    }
}
// Sidenav checkbox functions
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