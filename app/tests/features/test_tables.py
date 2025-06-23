from fastapi.testclient import TestClient
from io import BytesIO
import pandas as pd


def test_preview_table_file(authorized_client: dict):
    auth_client = authorized_client["client"]

    # Test with CSV
    csv_content = b"header1,header2\nvalue1,value2\nvalue3,value4"
    csv_file = ("preview.csv", BytesIO(csv_content), "text/csv")

    response_csv = auth_client.post("/api/v1/tables/preview", files={"file": csv_file})
    assert response_csv.status_code == 200, response_csv.text
    data_csv = response_csv.json()
    assert "header" in data_csv
    assert "data" in data_csv
    assert data_csv["header"] == ["header1", "header2"]
    assert data_csv["data"] == [["value1", "value2"], ["value3", "value4"]]

    # Test with XLSX
    xlsx_io = BytesIO()
    with pd.ExcelWriter(xlsx_io, engine="xlsxwriter") as writer:
        pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}).to_excel(
            writer, index=False, sheet_name="Sheet1"
        )
    xlsx_io.seek(0)
    xlsx_file = (
        "preview.xlsx",
        xlsx_io,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    response_xlsx = auth_client.post(
        "/api/v1/tables/preview", files={"file": xlsx_file}
    )
    assert response_xlsx.status_code == 200, response_xlsx.text
    data_xlsx = response_xlsx.json()
    assert data_xlsx["header"] == ["col1", "col2"]
    assert data_xlsx["data"] == [[1, 3], [2, 4]]


def test_preview_with_custom_rows(authorized_client: dict):
    auth_client = authorized_client["client"]
    csv_content = b"h1,h2\nr1,c1\nr2,c2\nr3,c3\nr4,c4\nr5,c5"
    csv_file = ("preview_rows.csv", BytesIO(csv_content), "text/csv")
    num_rows_to_preview = 3

    response = auth_client.post(
        "/api/v1/tables/preview",
        files={"file": csv_file},
        data={"preview_rows": num_rows_to_preview},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == num_rows_to_preview


def test_upload_table_for_user(authorized_client: dict):
    auth_client = authorized_client["client"]
    user_data = authorized_client["user_data"]

    # Create a dummy CSV file in memory
    file_content = b"col1,col2\n1,2\n3,4"
    file = ("test_table.csv", BytesIO(file_content), "text/csv")

    response = auth_client.post("/api/v1/tables/upload", files={"file": file})

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["table_name"] == "test_table"
    assert data["user_id"] == user_data["id"]


def test_upload_table_with_custom_name(authorized_client: dict):
    auth_client = authorized_client["client"]
    user_data = authorized_client["user_data"]

    file_content = b"colA,colB\n1,a\n2,b"
    file = ("original_name.csv", BytesIO(file_content), "text/csv")
    custom_name = "my_custom_table_name"

    response = auth_client.post(
        "/api/v1/tables/upload",
        files={"file": file},
        data={"table_name": custom_name},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["table_name"] == custom_name
    assert data["original_file_name"] == "original_name.csv"
    assert data["user_id"] == user_data["id"]


def test_upload_table_name_conflict(authorized_client: dict):
    auth_client = authorized_client["client"]

    # 1. Upload a table with a specific name
    file_content_1 = b"a,b\n1,2"
    file_1 = ("first.csv", BytesIO(file_content_1), "text/csv")
    custom_name = "conflicting_name"
    response_1 = auth_client.post(
        "/api/v1/tables/upload",
        files={"file": file_1},
        data={"table_name": custom_name},
    )
    assert response_1.status_code == 201

    # 2. Try to upload another table with the same name
    file_content_2 = b"c,d\n3,4"
    file_2 = ("second.csv", BytesIO(file_content_2), "text/csv")
    response_2 = auth_client.post(
        "/api/v1/tables/upload",
        files={"file": file_2},
        data={"table_name": custom_name},
    )
    assert response_2.status_code == 409
    assert "уже существует" in response_2.json()["detail"]


def test_upload_invalid_extension(authorized_client: dict):
    auth_client = authorized_client["client"]
    file_content = b"this is not a table"
    file = ("test.txt", BytesIO(file_content), "text/plain")
    response = auth_client.post("/api/v1/tables/upload", files={"file": file})
    assert response.status_code == 400
    assert "Неподдерживаемый тип файла" in response.json()["detail"]


def test_upload_excel_with_multiple_sheets(authorized_client: dict):
    auth_client = authorized_client["client"]
    excel_io = BytesIO()
    with pd.ExcelWriter(excel_io, engine="xlsxwriter") as writer:
        pd.DataFrame({"col1": [1]}).to_excel(writer, index=False, sheet_name="Sheet1")
        pd.DataFrame({"col2": [2]}).to_excel(writer, index=False, sheet_name="Sheet2")
    excel_io.seek(0)
    file = (
        "multisheet.xlsx",
        excel_io,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    response = auth_client.post("/api/v1/tables/upload", files={"file": file})
    assert response.status_code == 400
    assert "не поддерживаются" in response.json()["detail"]


def test_upload_empty_file(authorized_client: dict):
    auth_client = authorized_client["client"]
    file_content = b""
    file = ("empty.csv", BytesIO(file_content), "text/csv")
    response = auth_client.post("/api/v1/tables/upload", files={"file": file})
    assert response.status_code == 400
    assert "файл пуст" in response.json()["detail"]


def test_read_own_tables(authorized_client: dict):
    auth_client = authorized_client["client"]

    # Upload a table first
    file_content = b"col1,col2\n1,2\n3,4"
    file = ("my_second_table.csv", BytesIO(file_content), "text/csv")
    auth_client.post("/api/v1/tables/upload", files={"file": file})

    response = auth_client.get("/api/v1/tables/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Find the table we just uploaded
    uploaded_table = next(
        (t for t in data if t["table_name"] == "my_second_table"), None
    )
    assert uploaded_table is not None
    assert uploaded_table["user_id"] == authorized_client["user_data"]["id"]


def test_rename_table(authorized_client: dict):
    auth_client = authorized_client["client"]

    # 1. Upload a table
    file_content = b"a,b\n1,2"
    file = ("table_to_rename.csv", BytesIO(file_content), "text/csv")
    create_response = auth_client.post("/api/v1/tables/upload", files={"file": file})
    assert create_response.status_code == 201
    table_id = create_response.json()["id"]

    # 2. Rename the table
    new_name = "renamed_table"
    rename_response = auth_client.put(
        f"/api/v1/tables/{table_id}", json={"table_name": new_name}
    )
    assert rename_response.status_code == 200, rename_response.text
    renamed_data = rename_response.json()
    assert renamed_data["table_name"] == new_name
    assert renamed_data["id"] == table_id

    # 3. Verify the change by fetching all tables
    get_response = auth_client.get("/api/v1/tables/")
    tables = get_response.json()
    assert new_name in [t["table_name"] for t in tables]
    assert "table_to_rename" not in [t["table_name"] for t in tables]


def test_delete_table(authorized_client: dict):
    auth_client = authorized_client["client"]

    # Upload a table to delete
    file_content = b"col1,col2\n1,2\n3,4"
    file = ("table_to_delete.csv", BytesIO(file_content), "text/csv")
    create_response = auth_client.post("/api/v1/tables/upload", files={"file": file})
    table_id = create_response.json()["id"]

    delete_response = auth_client.delete(f"/api/v1/tables/{table_id}")
    assert delete_response.status_code == 200

    # Verify it's gone from the list
    get_response = auth_client.get("/api/v1/tables/")
    data = get_response.json()
    assert table_id not in [t["id"] for t in data]


def test_unauthorized_user_cannot_access_tables(client: TestClient):
    response = client.get("/api/v1/tables/")
    assert response.status_code == 401

    # Also check preview endpoint
    csv_content = b"h1,h2\nv1,v2"
    csv_file = ("unauth_preview.csv", BytesIO(csv_content), "text/csv")
    response_preview = client.post("/api/v1/tables/preview", files={"file": csv_file})
    assert response_preview.status_code == 401
