# Lab 2
## Madhumitha Balaji - 1004471

To start the application, run ```docker-compose up -d```

For visualizing the application, open up your browser and enter:
``` http://127.0.0.1/docs```


## Part 1 - Requests
The ```.http``` files can be found in the folder named checkoff
- GET with no query: ```get_no_query.http```
- GET with sortBy: ```get_sortBy.http```
- GET with offset: ```get_offset.http```
- GET with count: ```get_count.http```
- Combinations of the above: ```get_sortBy_offset.http``` and ```get_sortBy_offset_count.http```
- GET user by id: ```get_specific_id.http```
- POST user: ```post_user.http```
- DELETE user: ```delete_user.http```

## Part 2 - Idempotent Routes
Idempotence - making multiple identical requests has the same effect as making a single request
GET is idempotent as called several times in a row, the client gets the same results
DELETE is idempotent, the returned status code may change between requests but the client gets same results.
POST is not idempotent because if called multiple times, it will create multiple users

## Part 3 - Challenges

- User authentication
    - Click the green "Authorize" button at the top-right
    - Enter id (which was auto-generated on calling POST) as username
    - Enter the password set when user was created
- File upload in a POST request: /uploadfile allows you to choose a file that you want to upload


## Configuration and file structure
File structure is:
```
.
├── app
│   ├── Dockerfile
│   ├── __init__.py
│   ├── main.py
│   ├── requirements.txt
│   └── src
│       ├── __init__.py
│       ├── dependecies.py
│       ├── models.py
│       ├── routers.py
│       └── settings.py
└── docker-compose.yml
```
In the app directory in ```main.py``` file we make all the dependencies and routers importing from the same name files located in ```src``` directory.

```src``` directory is the one that containes all the needed pydantic models (models.py), database and authentication variables (settings.py). 

Authentication is made by using ```bearer``` scheme with ```token``` creation and usage.

```dependecies.py``` is the file containing authentication functions.


