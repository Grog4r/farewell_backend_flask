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

### Uploading and Managing Images

For uploading images you can access the endpoint `/uploader`.
It provides a simple web GUI for uploading images.

For managing uploaded images you can access the endpoint `/manage`.
There you will be able to viewm edit and delete currently uploaded images.

### Frontend API

There are three API endpoints needed for accessing the uploaded images:

- `GET /` will return a list of JSON objects representing the metadata of the images.
    The arg `only_unlocked` can be used to only show the metadata of unlocked images. Defaults to `False`.
    The arg `only_locked` can be used to only show the metadata of locked images. Defaults to `False`.
    **Only one of the arguments `only_locked` and `only_unlocked` can be set to true.**
- `GET /resource?uuid={uuid}` will return the image file for the provided uuid. The uuid can be found in the metadata of the images.
- `GET /meta?uuid={uuid}` will return the metadata for one image with the uuid `uuid`.

The fields in the metadata stand for the following:

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
