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
document.addEventListener('mouseup', function() {
    isHandlerDragging = false;
});
// Main panel
$('tbody').on('click', 'tr', function() {
    let key_name = document.getElementById('key_name');
    key_name.dataset.value = this.id;
    key_name.dataset.type = this.dataset.type;
    console.log(key_name.dataset.type);
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
    console.log('create_key: ', id);
    $.getJSON('/create_key/' + encodeURIComponent(id), function (result) {
        console.log(result);
        if(id.slice(-1) !== '\\') {
            id += '\\';
        }
        update_branch(id, true);
    });
}
function new_value() {
    let type = prompt('Enter value type (0 -> REG_SZ, 1 -> REG_MULTI_SZ, 2 -> REG_EXPAND, 3 -> REG_DWORD');
    let id = document.getElementById('key_name').dataset.name;
    let param = id + '\\\\value\\\\' + type;
    if(0 <= type && type <= 3) {
        $.getJSON('/create_value/' + encodeURIComponent(param), function (result) {
            update_branch(id + '\\', false);
            select_key(id);
        });
    } else {
        window.alert('Invalid type');
    }
}
function rename_key() {
    let id = document.getElementById('key_name').dataset.name;
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
    if(valid_name(check_name)) {
        check_name = id + '\\\\value\\\\' + new_name;
        // $.getJSON('/rename_key/' + encodeURIComponent(check_name), function (result) {
        //     console.log(result);
        //     update_branch(base_name + '\\', false);
        //     select_key(id);
        // });
    } else {
        window.alert('Key name not valid')
    }
}
function delete_key() {
    let id = document.getElementById('key_name').dataset.name;
    if(id.length > 2) {
        $.getJSON('/delete_key/' + encodeURIComponent(id), function (result) {
            id = id.slice(0, id.lastIndexOf('\\'));
            update_branch(id + '\\', false);
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
    let key_name = document.getElementById('key_name');
    let id = key_name.dataset.name;
    let new_value = '';
    if(key_name.dataset.type === 'REG_MULTI_SZ') {
        new_value = prompt('Enter strings - use "[\\end]" as delimiter');
    } else {
        new_value = prompt('Enter new value');
    }
    if(valid_value(key_name.dataset.type, new_value)) {
        let param = id + '\\\\value\\\\' + key_name.dataset.value + '\\\\data\\\\' + new_value;
        console.log(param);
        $.getJSON('/edit_value/' + encodeURIComponent(param), function (result) {
            update_branch(id + '\\', false);
            select_key(id);
        });
    } else {
        window.alert('Invalid value');
    }
}
function delete_value() {
    let key_name = document.getElementById('key_name');
    let id = key_name.dataset.name;
    let value = key_name.dataset.value;
    let string = id + '\\\\value\\\\' + value;
    $.getJSON('/delete_value/' + encodeURIComponent(string), function (result) {
        update_table();
    });
}
function valid_value(type, new_value) {
    if(type === 'REG_DWORD') {
        return new_value >= 0 && new_value <= 4294967295;
    }
    return true;
}
function update_table() {
    let value = document.getElementById('key_name').dataset.value
    value = document.getElementById(value);
    value.remove();
    value = document.getElementById('(default)');
    $(value)
        .toggleClass('selected')
        .siblings('.selected')
        .removeClass('selected');
    let key_name = document.getElementById('key_name');
    key_name.dataset.value = '(default)';
}
function update_branch(id, new_value) {
    let checkbox = document.getElementById(id);
    console.log(id);
    if(new_value) {
        checkbox.style.visibility = 'visible';
    }
    if(checkbox.checked === true) {
        remove_branch(id);
        expand_branch(id);
    }
}
function valid_name(name) {
    let parent_name = name.split('\\');
    parent_name.pop();
    parent_name = parent_name.join('\\') + '\\';
    let children = document.getElementById(parent_name + '\\sub').querySelectorAll('.child');
    name += '\\';
    for(let child in children) {
        if(children[child].id === name) {
            return false;
        }
    }
    return true;
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
    input.className = 'child';
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