from flask import Flask, render_template,jsonify, request
import crockpot

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/lookup')
def lookup():
    return app.send_static_file('lookup.html')

@app.route('/all_ingredients', methods=['GET'])
def all_ingredients():
    data = crockpot.ingredients
    for d in data:
        d['Info'] = ', '.join([crockpot.FOOD_TYPES[i]+
                              '='+
                              str(d['FoodTypes'][i]) for i in range(len(crockpot.FOOD_TYPES)) if d['FoodTypes'][i]!=0])
    return jsonify(data)

@app.route('/all_dishes', methods=['GET'])
def all_dishes():
    return jsonify(crockpot.dishes)

@app.route('/get_recipe/<string:ids>', methods=['GET'])
def get_recipe(ids:str):
    myIDs = [int(i) for i in ids.split('&')]
    myrecipe = crockpot.find_recipes(myIDs)
    mydish = [[d for d in crockpot.dishes if d['DishID'] == r['DishID']][0] for r in myrecipe]
    return jsonify(mydish)

@app.route('/get_best_recipe/<string:inputs>', methods=['GET'])
def get_best_recipe(inputs:str):
    myIDs=[]
    myinputs = inputs.split('&')
    for myinput in myinputs:
        myinput_parsed = myinput.split('=')
        myIDs +=[int(myinput_parsed[0])]*int(myinput_parsed[1])
    myrecipes = crockpot.find_best_recipes(myIDs)
    return jsonify(myrecipes)

if __name__=='__main__':
    app.run()
