from fastapi.testclient import TestClient


def create(client: TestClient, resource: str, payload: dict) -> dict:
    response = client.post(f"/v1/{resource}", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_user_crud(client: TestClient) -> None:
    user = create(client, "users", {"email": "ivan@example.com", "display_name": "Иван"})
    assert user["role"] == "operator"
    assert user["created_at"]

    assert client.get(f"/v1/users/{user['id']}").status_code == 200
    assert len(client.get("/v1/users").json()) == 1

    response = client.patch(f"/v1/users/{user['id']}", json={"role": "admin"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert response.json()["display_name"] == "Иван"  # PATCH не трогает другие поля

    response = client.delete(f"/v1/users/{user['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/v1/users/{user['id']}").status_code == 404


def test_validation_errors_return_422(client: TestClient) -> None:
    bad_payloads = [
        ("users", {"email": "not-an-email", "display_name": "X"}),
        ("users", {"email": "a@b.co", "display_name": "X", "role": "boss"}),
        ("users", {"id": 5, "email": "a@b.co", "display_name": "X"}),  # служебное поле
        ("labels", {"name": "bug", "color": "red"}),
        ("projects", {"name": ""}),
    ]
    for resource, payload in bad_payloads:
        response = client.post(f"/v1/{resource}", json=payload)
        assert response.status_code == 422, (resource, payload, response.text)


def test_not_found_returns_404(client: TestClient) -> None:
    for resource in ("users", "projects", "labels", "tasks", "comments"):
        assert client.get(f"/v1/{resource}/999").status_code == 404
        assert client.patch(f"/v1/{resource}/999", json={}).status_code == 404
        assert client.delete(f"/v1/{resource}/999").status_code == 404


def test_conflicts_return_409(client: TestClient) -> None:
    create(client, "users", {"email": "dup@example.com", "display_name": "A"})
    response = client.post("/v1/users", json={"email": "dup@example.com", "display_name": "B"})
    assert response.status_code == 409

    create(client, "labels", {"name": "bug"})
    assert client.post("/v1/labels", json={"name": "bug"}).status_code == 409

    # ссылка на несуществующий проект
    response = client.post("/v1/tasks", json={"project_id": 999, "title": "X"})
    assert response.status_code == 409


def test_full_scenario(client: TestClient) -> None:
    """Сценарий из раздела «Как проверить работу»."""
    user = create(client, "users", {"email": "ivan@example.com", "display_name": "Иван"})
    project = create(client, "projects", {"name": "TaskFlow"})
    label = create(client, "labels", {"name": "bug"})
    assert label["color"] == "#6b7280"

    task = create(
        client,
        "tasks",
        {
            "project_id": project["id"],
            "assignee_id": user["id"],
            "label_id": label["id"],
            "title": "Настроить Docker",
        },
    )
    assert task["status"] == "open"
    assert task["priority"] == "medium"

    comment = create(
        client, "comments", {"task_id": task["id"], "author_id": user["id"], "body": "Начал"}
    )

    # фильтры
    response = client.get("/v1/tasks", params={"project_id": project["id"], "status": "open"})
    assert [t["id"] for t in response.json()] == [task["id"]]
    assert client.get("/v1/tasks", params={"status": "done"}).json() == []
    response = client.get("/v1/comments", params={"task_id": task["id"]})
    assert [c["id"] for c in response.json()] == [comment["id"]]

    # смена статуса
    response = client.patch(f"/v1/tasks/{task['id']}", json={"status": "done"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"
    assert response.json()["title"] == "Настроить Docker"

    # автора комментария удалить нельзя
    assert client.delete(f"/v1/users/{user['id']}").status_code == 409

    # удаление проекта удаляет задачи и комментарии
    assert client.delete(f"/v1/projects/{project['id']}").status_code == 204
    assert client.get("/v1/tasks").json() == []
    assert client.get("/v1/comments").json() == []

    # остальные данные на месте
    assert client.get(f"/v1/users/{user['id']}").status_code == 200
    assert client.get(f"/v1/labels/{label['id']}").status_code == 200


def test_delete_label_and_user_set_null(client: TestClient) -> None:
    user = create(client, "users", {"email": "u@example.com", "display_name": "U"})
    project = create(client, "projects", {"name": "P"})
    label = create(client, "labels", {"name": "feature", "color": "#22C55E"})
    task = create(
        client,
        "tasks",
        {
            "project_id": project["id"],
            "assignee_id": user["id"],
            "label_id": label["id"],
            "title": "T",
        },
    )

    assert client.delete(f"/v1/labels/{label['id']}").status_code == 204
    assert client.delete(f"/v1/users/{user['id']}").status_code == 204

    task_after = client.get(f"/v1/tasks/{task['id']}").json()
    assert task_after["label_id"] is None
    assert task_after["assignee_id"] is None
