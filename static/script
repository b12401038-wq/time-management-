let dragging = false;
let selectedCells = [];
let colorMap = {};

document.querySelectorAll(".cell").forEach(cell => {
    cell.addEventListener("mousedown", () => {
        dragging = true;
        toggleSelect(cell);
    });

    cell.addEventListener("mouseover", () => {
        if (dragging) toggleSelect(cell);
    });

    cell.addEventListener("mouseup", () => {
        dragging = false;
        editSelected();
    });
});

function toggleSelect(cell) {
    cell.style.outline = "2px solid pink";
    selectedCells.push(cell);
}

function editSelected() {
    let name = prompt("輸入課程名稱：");
    if (!name) {
        selectedCells.forEach(c => c.style.outline = "");
        selectedCells = [];
        return;
    }

    if (!(name in colorMap)) colorMap[name] = randomColor();

    selectedCells.forEach(c => {
        c.textContent = name;
        c.style.backgroundColor = colorMap[name];
        c.style.outline = "";
    });

    selectedCells = [];
    detectConflict();
}

function randomColor() {
    return `hsl(${Math.random()*360}, 70%, 80%)`;
}

function detectConflict() {
    const map = {};
    document.querySelectorAll(".cell").forEach(c => {
        const key = c.dataset.day + "-" + c.dataset.period;
        const name = c.textContent.trim();
        if (!name) return;

        if (!map[key]) map[key] = [];
        map[key].push(c);
    });

    document.querySelectorAll(".cell").forEach(c => c.classList.remove("conflict"));

    for (let key in map) {
        if (map[key].length > 1) {
            map[key].forEach(c => c.classList.add("conflict"));
        }
    }
}

document.getElementById("saveBtn").onclick = () => {
    let data = [];

    document.querySelectorAll(".cell").forEach(c => {
        if (c.textContent.trim() !== "") {
            data.push({
                day: c.dataset.day,
                period: c.dataset.period,
                name: c.textContent.trim()
            });
        }
    });

    fetch("/save", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    alert("儲存完成");
};

function exportPNG() {
    window.open("/export_png");
}
