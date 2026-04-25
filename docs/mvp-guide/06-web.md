# 6. Визуализация дерева — Web

---

### MVP-WEB-01 — HTML-страница-шаблон + подключение vis.js через CDN

```html path=app/templates/tree.html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Family Tree</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        #tree-container { width: 100vw; height: 100vh; border: 1px solid lightgray; }
        #person-modal { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                        background: white; padding: 24px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    </style>
</head>
<body>
    <div id="tree-container"></div>
    <div id="person-modal">
        <h2 id="modal-name"></h2>
        <p id="modal-birth"></p>
        <p id="modal-death"></p>
        <p id="modal-gender"></p>
        <p id="modal-bio"></p>
        <button onclick="closeModal()">Закрыть</button>
    </div>
    <script src="/static/tree.js"></script>
</body>
</html>
```

---

### MVP-WEB-02 — Рендеринг дерева: загрузка данных из API, создание графа vis.js

```javascript path=app/static/tree.js
async function loadTree() {
    const token = localStorage.getItem('access_token');
    const response = await fetch('/api/tree', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();

    const nodes = new vis.DataSet(data.nodes.map(n => ({
        id: n.id,
        label: n.label,
        color: {
            background: n.gender === 'male' ? '#ADD8E6' : n.gender === 'female' ? '#FFB6C1' : '#D3D3D3',
            border: n.is_alive ? '#333' : '#808080',
        },
        borderWidth: n.is_alive ? 1 : 2,
        shapeProperties: { borderDashes: !n.is_alive },
    })));

    const edges = new vis.DataSet(data.edges.map(e => ({
        from: e.from,
        to: e.to,
        arrows: e.type === 'parent' ? 'to' : undefined,
        color: { color: e.type === 'spouse' ? '#e91e63' : '#666' },
        dashes: e.type === 'sibling',
    })));

    const container = document.getElementById('tree-container');
    const network = new vis.Network(container, { nodes, edges }, {
        layout: { hierarchical: { direction: 'UD', sortMethod: 'directed' } },
        interaction: { navigationButtons: true, zoomView: true, dragView: true },
    });

    // Клик по узлу → карточка (MVP-WEB-03)
    network.on('click', async function(params) {
        if (params.nodes.length > 0) {
            const personId = params.nodes[0];
            const resp = await fetch(`/api/persons/${personId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const person = await resp.json();
            showPersonModal(person);
        }
    });

    return network;
}

function showPersonModal(person) {
    document.getElementById('modal-name').textContent = `${person.last_name} ${person.first_name} ${person.middle_name || ''}`;
    document.getElementById('modal-birth').textContent = person.date_birth ? `Рождение: ${person.date_birth}` : '';
    document.getElementById('modal-death').textContent = person.date_death ? `Смерть: ${person.date_death}` : '';
    document.getElementById('modal-gender').textContent = `Пол: ${person.gender || 'не указан'}`;
    document.getElementById('modal-bio').textContent = person.biography || '';
    document.getElementById('person-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('person-modal').style.display = 'none';
}

loadTree();
```

---

### MVP-WEB-03 — Клик по узлу → модальное окно с данными персоны

Уже реализовано в `tree.js` выше (обработчик `network.on('click')` + `showPersonModal()`).

---

### MVP-WEB-04 — Цветовое кодирование по полу и статусу жив/умер

Уже реализовано в `tree.js` выше (в `nodes.map()` — `color.background` по полу, `borderDashes` для умерших).
