let editingTaskId = null;
let currentFilter = "all";

document.addEventListener("DOMContentLoaded", () => {
    loadTasks("all");
});

/* ================= TASKS ================= */

async function loadTasks(filter = "all") {
    currentFilter = filter;

    const res = await fetch("/tasks", {
        headers: {
            "Authorization": "Bearer " + localStorage.getItem("token")
        }
    });

    if (!res.ok) {
        console.error("Не удалось загрузить задачи");
        return;
    }

    const tasks = await res.json();
    const list = document.getElementById("tasks");
    list.innerHTML = "";

    let total = 0;
    let done = 0;

    tasks.forEach(task => {
        if (filter !== "all" && task.quadrant !== filter) return;

        total++;
        if (task.completed) done++;

        const li = document.createElement("li");
        li.className = "task-item";

        /* Левая часть */
        const left = document.createElement("div");
        left.className = "task-left";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = task.completed;

        checkbox.onclick = (e) => {
            e.stopPropagation();
            toggleTask(task.id, checkbox.checked);
        };

        const title = document.createElement("span");
        title.className = "task-title";
        if (task.completed) title.classList.add("done");

        title.innerText = `${task.title} [${task.quadrant}]`;

        left.appendChild(checkbox);
        left.appendChild(title);

        /* Кнопка удаления */
        const deleteBtn = document.createElement("button");
        deleteBtn.className = "task-delete";
        deleteBtn.innerText = "✖";

        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteTask(task.id);
        };

        li.appendChild(left);
        li.appendChild(deleteBtn);

        li.onclick = () => openEditTask(task);

        list.appendChild(li);
    });

    document.getElementById("stat-total").innerText = total;
    document.getElementById("stat-done").innerText = done;
    document.getElementById("stat-active").innerText = total - done;
}

async function toggleTask(id, completed) {
    await fetch(`/tasks/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + localStorage.getItem("token")
        },
        body: JSON.stringify({ completed })
    });

    loadTasks(currentFilter);
}

/* ================= MODAL ================= */

function openTaskModal() {
    editingTaskId = null;

    document.getElementById("taskTitle").value = "";
    document.getElementById("taskDescription").value = "";
    document.getElementById("taskDeadline").value = "";
    document.getElementById("taskImportant").checked = false;

    document.getElementById("taskModal").style.display = "flex";
}

function openEditTask(task) {
    editingTaskId = task.id;

    document.getElementById("taskTitle").value = task.title;
    document.getElementById("taskDescription").value = task.description || "";

    // 👇 ВАЖНО: backend -> deadline_at
    document.getElementById("taskDeadline").value =
        task.deadline_at ? task.deadline_at.split("T")[0] : "";

    document.getElementById("taskImportant").checked = task.is_important;

    document.getElementById("taskModal").style.display = "flex";
}

function closeTaskModal() {
    document.getElementById("taskModal").style.display = "none";
}

/* ================= SAVE ================= */

async function saveTask() {
    const title = document.getElementById("taskTitle").value.trim();
    const description = document.getElementById("taskDescription").value;
    const deadlineValue = document.getElementById("taskDeadline").value;
    const is_important = document.getElementById("taskImportant").checked;

    if (!title || !deadlineValue) {
        alert("Название и дата обязательны");
        return;
    }

    const deadline_at = new Date(deadlineValue).toISOString();

    const data = {
        title,
        description,
        deadline_at,
        is_important
    };

    const url = editingTaskId
        ? `/tasks/${editingTaskId}`
        : "/tasks/";

    const method = editingTaskId ? "PUT" : "POST";

    const res = await fetch(url, {
        method,
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + localStorage.getItem("token")
        },
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        const text = await res.text();
        alert("Ошибка сохранения задачи:\n" + text);
        return;
    }

    closeTaskModal();
    editingTaskId = null;
    loadTasks(currentFilter);
}



/* ================= PROFILE ================= */

function openProfile() {
    const modal = document.getElementById("profileModal");
    modal.style.display = "flex";

    fetch("/auth/me", {
        headers: {
            "Authorization": "Bearer " + localStorage.getItem("token")
        }
    })
    .then(res => {
        if (!res.ok) throw new Error("Не удалось загрузить профиль");
        return res.json();
    })
    .then(user => {
        document.getElementById("profileEmail").innerText = user.email;
        document.getElementById("profileNickname").value = user.nickname;
    })
    .catch(err => {
        alert(err.message);
        modal.style.display = "none";
    });
}

function closeProfile() {
    document.getElementById("profileModal").style.display = "none";
}

async function saveProfile() {
    const nickname = document.getElementById("profileNickname").value;
    const password = document.getElementById("newPassword").value;

    const res = await fetch("/auth/me", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + localStorage.getItem("token")
        },
        body: JSON.stringify({ nickname, password })
    });

    if (!res.ok) {
        alert("Ошибка обновления профиля");
        return;
    }

    closeProfile();
}


function logout() {
    localStorage.removeItem("token");
    window.location.href = "/login";
}

async function deleteTask(id) {
    if (!confirm("Удалить задачу?")) return;

    await fetch(`/tasks/${id}`, {
        method: "DELETE",
        headers: {
            "Authorization": "Bearer " + localStorage.getItem("token")
        }
    });

    loadTasks(currentFilter);
}
