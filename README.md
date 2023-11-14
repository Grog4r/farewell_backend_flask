# Farewell for Flo

This is a very simple Flask App that implements the following:

- A simple HTML Frontend for uploading and managing Images
- Backend endpoints for retrieving Images

## Set Up

To run this application you need to install the following:

- python 3.11
- docker-compose

You will then be able to run the application with

```bash
sudo docker compose build --no-cache && sudo docker compose up
```

## Usage

### Frontend

For uploading images you will need to access `http://127.0.0.1:8000/uploader`.

For managing uploaded images you will need to access `http://127.0.0.1:8000/manage`.

The username and password are currently `john` and `matrix`.

### Backend API

There are two API endpoints needed for accessing the uploaded images:

- `GET /` will return a list of JSON objects representing the metadata of the images.
- `GET /resource?uuid={uuid}` will return an image file from the provided uuid. The uuid can be found in the metadata of the images.

The fiels in the metadata stand for the following:

- `uuid`: The uuid linking the metadata to the image file.
    The uuid is created by the backend when the image is uploaded.
- `file_name`: The name of the image file.
    This is the original name of the image file.
- `creation_date`: The date the image was taken.
    This is automatically read from the image file when uploaded.
- `unlock_date`: The date the image should be unlocked at.
    This date is calculated automatically from the creation date.
- `title`: The title of the image.
    This is entered by the user in the frontend.
- `caption`: The caption of the image.
    This is entered by the user in the frontend.
- `uploaded_by`: The name of the person who uploaded the image.
    This is entered by the user in the frontend.
