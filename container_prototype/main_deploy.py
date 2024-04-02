from models.model_definitions import MLflowModelGetter
import os, json, time
import random

model_getter = MLflowModelGetter(model_name="torch_model", model_version="champion")

if __name__ == "__main__":
    model = model_getter.get_model()  # returns mlflow.pyfunc.PyFuncModel

    print("Model is running")
    while True:

        random_input = {"x1": random.random(), "x2": random.random()}
        time.sleep(1)
        print(random_input)
        print(model.evaluate(random_input))
