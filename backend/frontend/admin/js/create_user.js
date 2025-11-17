document.getElementById("createUserForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
        name: document.getElementById("cuName").value,
        email: document.getElementById("cuEmail").value,
        password: document.getElementById("cuPassword").value,
        phone: document.getElementById("cuPhone").value,
    };

    const res = await fetch("/api/admin/create-user", {
        method: "POST",
        headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (res.ok) {
        alert("User Created Successfully!");
        document.getElementById("createUserForm").reset();
    } else {
        alert(data.error || "Error creating user");
    }
});
