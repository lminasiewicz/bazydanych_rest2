from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

uri = os.getenv("URI")
user = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test1234"), database="neo4j")


# GET EMPLOYEES


def get_employees(tx):
    query = "match (e:Employee) return e"
    results = tx.run(query).data()
    if not results:
        return None
    else:
        return [{"name": result["e"]["name"], "surname": result["e"]["surname"], "age": result["e"]["age"]} for result in results]


@app.route("/employees", methods=["GET"])
def get_employees_route():
    employees = driver.session().read_transaction(get_employees)
    print("Received a GET request on endpoint /employees")
    return jsonify({"employees": employees}), 200


# ADD EMPLOYEE


def add_employee(tx, name, surname, age):
    query = f"CREATE (p:Employee {{name: \"{name}\", surname: \"{surname}\", age: \"{age}\"}})"
    tx.run(query)


@app.route('/employees', methods=['POST'])
def add_employee_route():
    req = request.json
    name = req["name"]
    surname = req["surname"]
    age = req["age"]

    driver.session().write_transaction(add_employee, name, surname, age)
    print("Received a POST request on endpoint /employees")

    response = {'status': 'success'}
    return jsonify(response), 200


# UPDATE EMPLOYEE


def update_employee(tx, id, name, surname, age):
    query = f"MATCH (e:Employee) WHERE ID(e)={id} RETURN e"
    result = tx.run(query).data()

    if not result:
        return None
    else:
        query = f"MATCH (e:Employee) WHERE ID(e)={id} SET e.name = \"{name}\", e.surname = \"{surname}\", e.age = \"{age}\""
        tx.run(query)
        return {'name': name, 'surname': surname, 'age': age}


@app.route('/employees/<int:id>', methods=['PUT'])
def update_movie_route(id):
    req = request.json
    name = req["name"]
    surname = req["surname"]
    age = req["age"]

    employee = driver.session().write_transaction(update_employee, id, name, surname, age)
    print("Received a PUT request on endpoint /employees/<id>")

    if not employee:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response), 200


# DELETE EMPLOYEE


def delete_employee(tx, id):
    query = f"MATCH (e:Employee) WHERE ID(e)={id} RETURN e"
    result = tx.run(query).data()

    if not result:
        return None
    else:
        query = f"MATCH (e:Employee) WHERE ID(e)={id} DETACH DELETE e"
        tx.run(query)
        return {'id': id}


@app.route('/employees/<int:id>', methods=['DELETE'])
def delete_employee_route(id):
    employee = driver.session().write_transaction(delete_employee, id)

    if not employee:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response), 200


# GET SUBORDINATES


def get_subordinates(tx, id):
    query = f"match (e:Employee)-[:MANAGES]->(d:Department) WHERE ID(e) = {id} return d"
    results = tx.run(query).data()
    if not results:
        return None
    else:
        query = f"match (e:Employee)-[:WORKS_IN]->(d:Department) WHERE d.name = \"{results[0]['d']['name']}\" return e"
        results = tx.run(query).data()
        return [{"name": result["e"]["name"], "surname": result["e"]["surname"], "age": result["e"]["age"]} for result in results]


@app.route("/employees/<int:id>/subordinates", methods=["GET"])
def get_subordinates_route(id):
    employees = driver.session().read_transaction(get_subordinates, id)
    print("Received a GET request on endpoint /employees/<id>/subordinates")
    return jsonify({"employees": employees}), 200


# GET DEPT INFO BY EMPLOYEE


def get_dept_info_by_employee(tx, id):
    query = f"match (e:Employee)-[:WORKS_IN]->(d:Department) WHERE ID(e) = {id} return d"
    results = tx.run(query).data()
    if not results:
        return None
    else:
        dept_name = results[0]['d']['name']
        query1 = f"match (e:Employee)-[:WORKS_IN]->(d:Department) WHERE d.name = \"{dept_name}\" return count(e)"
        results = tx.run(query1).data()
        query2 = f"match (e:Employee)-[:MANAGES]->(d:Department) WHERE d.name = \"{dept_name}\" return e"
        results2 = tx.run(query2).data()[0]
        return {"name": dept_name, "employee_count": results[0]["count(e)"], "manager": f"{results2['e']['name']} {results2['e']['surname']}"}


@app.route("/employees/<int:id>/dept_info", methods=["GET"])
def get_dept_info_by_employee_route(id):
    info = driver.session().read_transaction(get_dept_info_by_employee, id)
    print("Received a GET request on endpoint /employees/<id>/dept_info")
    return jsonify({"department": info}), 200


# GET DEPARTMENTS


def get_departments(tx):
    query = "match (d:Department) return d"
    results = tx.run(query).data()
    if not results:
        return None
    else:
        return [{"name": result["d"]["name"], "address": result["d"]["address"], "city": result["d"]["city"]} for result in results]


@app.route("/departments", methods=["GET"])
def get_departments_route():
    departments = driver.session().read_transaction(get_departments)
    print("Received a GET request on endpoint /departments")
    return jsonify({"departments": departments}), 200


# GET EMPLOYEES WORKING IN A DEPARTMENT

def get_employees_by_dept(tx, id):
    query = f"match (e:Employee)-[r]->(d:Department) WHERE ID(d) = {id} return e"
    results = tx.run(query).data()
    if not results:
        return None
    else:
        return [{"name": result["e"]["name"], "surname": result["e"]["surname"], "age": result["e"]["age"]} for result in results]


@app.route("/departments/<int:id>/employees", methods=["GET"])
def get_employees_by_dept_route(id):
    employees = driver.session().read_transaction(get_employees_by_dept, id)
    print("Received a GET request on endpoint /departments/<id>/employees")
    return jsonify({"department employees": employees}), 200


if __name__ == "__main__":
    app.run()