document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("createUserForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            name: document.getElementById("cuName").value.trim(),
            email: document.getElementById("cuEmail").value.trim(),
            password: document.getElementById("cuPassword").value.trim(),
            phone: document.getElementById("cuPhone").value.trim(),
        };

        // Basic validation
        if (!payload.name || !payload.email || !payload.password) {
            auth.showNotification("All fields except phone are required", "error");
            return;
        }

        try {
            const res = await auth.makeAuthenticatedRequest(
                "/api/admin/create-user",
                {
                    method: "POST",
                    body: JSON.stringify(payload),
                }
            );

            const data = await res.json();

            if (res.ok) {
                auth.showNotification("User created successfully!", "success");
                form.reset();
            } else {
                auth.showNotification(data.error || "Error creating user", "error");
            }
        } catch (err) {
            console.error("Create User Error:", err);
            auth.showNotification("Server error while creating user", "error");
        }
    });
});
