import csv
import itertools
from itertools import combinations
import os

FOOD_TYPES = ('Fruit','Meat','Fish','Veg','Egg','Sweet','Dairy','Monster','Inedible')
BENEFITS = ('Health','Hunger','Sanity')
ITEM_COUNT = 4
mydir = os.path.dirname(os.path.realpath(__file__))

with open(mydir+'/data/ingredients.csv', mode='r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    ingredients = []
    next(reader)
    for row in reader:
        ingredients.append({
            'IngID':int(row[0]),
            'CatID':int(row[1]),
            'Name':row[2],
            'FoodTypes':[float(x) if x!='' else 0 for x in row[3:len(FOOD_TYPES)+3]],
            'Cooked':''!=row[-len(BENEFITS)-1],
            'Benefits':[float (x) for x in row[(-len(BENEFITS)):]]
            })

with open(mydir+'/data/categories.csv', mode='r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    categories = []
    next(reader)
    for row in reader:
        categories.append({
            'CatID': int(row[0]),
            'Category': row[1],
            'FoodTypes':[float(x) if x!='' else 0 for x in row[2:-1]],
            'Cooked':row[-1]
        })

with open(mydir+'/data/dishes.csv', mode='r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    dishes = []
    next(reader)
    for row in reader:
        dishes.append({
            'DishID':int(row[0]),
            'Dish':row[1],
            'Benefits':[float(x) for x in row[2:len(BENEFITS)+2]],
            'MaxPerishDays':float(row[-3]),
            'CookSecs':float(row[-2]),
            'Priority':float(row[-1])
            })

with open(mydir+'/data/recipes.csv', mode='r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    recipes = []
    next(reader)
    for row in reader:
        recipes.append({
            'RcpID':int(row[0]),
            'DishID':int(row[1]),
            'Dish':row[2],
            'MinFoodTypes':[float(x) if x!='' else 0 for x in row[3:len(FOOD_TYPES)+3]],
            'MaxFoodTypes':[float(x) if x!='' else 100 for x in row[len(FOOD_TYPES)+3:len(FOOD_TYPES)*2+3]],
            'CanUseCookedIngredients':row[-3]=='',
            'Ingredient':list(map(int, row[-2].split(';'))) if row[-2]!='' else [-1],
            'IngredientExclude':set(map(int, row[-1].split(';'))) if row[-1]!='' else {-1}
            })
             
def find_recipes(IngIDs):
    myingredients = [[ing for ing in ingredients if ing['IngID']==id] for id in IngIDs]
    myfoodtypes = [myingredients[i][0]['FoodTypes'] for i in range(len(myingredients))]
    sumfoodtypes = [sum(f) for f in zip(*myfoodtypes)]
    has_cooked_ingredients = any([ing[0]['Cooked'] for ing in myingredients])
    filtered_recipes = []
    for r in recipes:
        if has_cooked_ingredients and (not r['CanUseCookedIngredients']):
            continue
        if r['IngredientExclude'] & set(IngIDs):
            continue
        if r['Ingredient']!=[-1] and not all([r['Ingredient'].count(i)<=IngIDs.count(i) for i in set(r['Ingredient'])]):
            continue
        if all(x>=x_min and x<=x_max for x,x_min,x_max in zip(sumfoodtypes, r['MinFoodTypes'], r['MaxFoodTypes'])):
            #found a recipe!
            filtered_recipes.append(r)  
    
    filtered_dishIDs = [filtered_recipes[i]['DishID'] for i in range(len(filtered_recipes))]
    filtered_dishes = [d for d in dishes if d['DishID'] in filtered_dishIDs]
    
    max_priority = max([filtered_dishes[i]['Priority'] for i in range(len(filtered_dishes))])
    priority_dishIDs = [d['DishID'] for d in filtered_dishes if d['Priority']==max_priority]
    priority_recipes = [f for f in filtered_recipes if f['DishID'] in priority_dishIDs]
    
    return priority_recipes

def find_all_ingredients(RcpID, IngIDs):
    myrecipe = [r for r in recipes if r['RcpID']==RcpID][0]
    
    #add required ingredients first
    item_count_needed = ITEM_COUNT - len(IngIDs)
    IngIDs_added = IngIDs[:]
    if myrecipe['Ingredient']!=[-1]:
        musthaves = [(i,myrecipe['Ingredient'].count(i)-IngIDs.count(i)) for i in set(myrecipe['Ingredient'])]
        if sum([m[1] for m in musthaves]) > item_count_needed:
            return {'IngIDs':[], 'Success': 0}
        else:
            for m in musthaves:
                IngIDs_added += [m[0]]*m[1]
            item_count_needed = ITEM_COUNT - len(IngIDs_added)
    
    #check current list of ingredients before iterating through all possible combos
    myingredients = [[ing for ing in ingredients if ing['IngID']==id] for id in IngIDs_added]
    myfoodtypes = [myingredients[i][0]['FoodTypes'] for i in range(len(myingredients))]
    sumfoodtypes = [sum(x) for x in zip(*myfoodtypes)]
    has_cooked_ingredients = any([ing[0]['Cooked'] for ing in myingredients])              
    
    if has_cooked_ingredients and not myrecipe['CanUseCookedIngredients']:
        return [{'IngIDs':[], 'Success': 0}]
    
    if myrecipe['IngredientExclude'] & set(IngIDs_added):
        return [{'IngIDs':[], 'Success': 0}]
    
    if any(x>x_max for x,x_max in zip(sumfoodtypes, myrecipe['MaxFoodTypes'])):
        return [{'IngIDs':[], 'Success': 0}]
    
    output = []
    #recursive function
    #each step picks 1 ingredient that satisfies all constaints and 
    #has at least 1 food type the recipe needs
    #until we get 4 ingredients to feed into the recipe
    #then check if the dish can be made (i.e. has highest priority)
    def update_func(IngIDs_update, sumfoodtypes_update):
        if len(IngIDs_update) == ITEM_COUNT:
            recipes_found = find_recipes(IngIDs_update)   
            if RcpID in [r['RcpID'] for r in recipes_found]:
                output.append({'IngIDs':IngIDs_update,'Success':100/len(recipes_found)})
        else:
            foodtype_add_min = [max(0,x_min-x_now) for x_now,x_min in zip(sumfoodtypes_update, myrecipe['MinFoodTypes'])]
            foodtype_add_max = [x_max-x_now for x_now,x_max in zip(sumfoodtypes_update, myrecipe['MaxFoodTypes'])]
            for ing in ingredients:
                if not myrecipe['CanUseCookedIngredients'] and ing['Cooked']==1:
                    continue
                if ing['IngID'] in myrecipe['IngredientExclude']:
                    continue
                if any(x>x_add_max for x,x_add_max in zip(ing['FoodTypes'], foodtype_add_max)):
                    continue
                if all(x_add_min==0 for x_add_min in foodtype_add_min) or \
                    any(x>0 and x_add_min>0 for x, x_add_min in zip(ing['FoodTypes'], foodtype_add_min)):
                    update_func(IngIDs_update = IngIDs_update+[ing['IngID']], 
                        sumfoodtypes_update = [x+x_now for x,x_now in zip(ing['FoodTypes'],sumfoodtypes_update)])
                
    update_func(IngIDs_added, sumfoodtypes)
    if len(output)==0:
        return [{'IngIDs':[], 'Success': 0}]
    else:
        return output

def find_best_recipes(IngIDs):
    IngIDs_comb = set(combinations(IngIDs, ITEM_COUNT))
    best_recipes = [
        {'Type':BENEFITS[0], 'Value':0, 'Dish':{'DishName':'', 'IngNames':[], 'IngRawBenefits':[0,0,0] }},
        {'Type':BENEFITS[1], 'Value':0, 'Dish':{'DishName':'', 'IngNames':[], 'IngRawBenefits':[0,0,0] }},
        {'Type':BENEFITS[2], 'Value':0, 'Dish':{'DishName':'', 'IngNames':[], 'IngRawBenefits':[0,0,0] }}
    ]
    
    #find best recipe that gives highest value in one of the 3 benefits
    #if multiple combos of ingredients yield same dish / benefit
    #select the combo that has lowest benefit when eating directly
    #if this is also the same,
    #select the combo that has lowest SUM of benefits when eating directly
    for ings in IngIDs_comb:
        myingredients = [[ing for ing in ingredients if ing['IngID']==id][0] for id in ings]
        ing_names = [ing['Name'] for ing in myingredients]
        raw_benefits = [sum(x) for x in zip(*[ing['Benefits'] for ing in myingredients])]
        myrecipes = find_recipes(ings)
        mydishes = [d for d in dishes if d['DishID'] in  [r['DishID'] for r in myrecipes]]
        benefits_expected =  [sum(x)/len(x) for x in zip(*[d['Benefits'] for d in mydishes])]
        mydishname = ' or '.join([d['Dish'] for d in mydishes])
        for i in range(len(BENEFITS)):
            if benefits_expected[i] > best_recipes[i]['Value']:
                best_recipes[i]['Value'] = benefits_expected[i]
                best_recipes[i]['Dish'] = {
                    'DishName': mydishname, 
                    'IngNames': ing_names,
                    'IngRawBenefits': raw_benefits
                    }
            else:
                if benefits_expected[i] == best_recipes[i]['Value']:
                    if raw_benefits[i] < best_recipes[i]['Dish']['IngRawBenefits'][i]:
                        best_recipes[i]['Dish'] = {
                            'DishName': mydishname, 
                            'IngNames':ing_names,
                            'IngRawBenefits': raw_benefits
                            }
                    else:
                        if raw_benefits[i] == best_recipes[i]['Dish']['IngRawBenefits'][i]:
                             if sum(raw_benefits) < sum(best_recipes[i]['Dish']['IngRawBenefits']):
                                best_recipes[i]['Dish'] = {
                                'DishName': mydishname, 
                                'IngNames':ing_names,
                                'IngRawBenefits': raw_benefits
                                }
    return best_recipes

def find_recipes_wrap(ingredient_names):
    IngIDs =  [[ing['IngID'] for ing in ingredients if ing['Name']==n][0] for n in ingredient_names]
    return find_recipes(IngIDs)

def find_all_ingredients_wrap(dish, ingredient_names):
    RcpIDs = [r['RcpID'] for r in recipes if r['Dish']==dish]
    IngIDs = [[ing['IngID'] for ing in ingredients if ing['Name']==n][0] for n in ingredient_names]
    #there can be multiple recipes per dish
    all_ingredients = []
    for i in RcpIDs:
        all_ingredients+=(find_all_ingredients(i,IngIDs))
    
    #summarize
    cutoff = 5
    ingredients_summary = []
    category_ingredients = [(c['Category'], set(ing['IngID'] for ing in ingredients if ing['CatID']==c['CatID'])) for c in categories] 
    all_success = sorted(set([a['Success'] for a in all_ingredients]), reverse=True)
    for success in all_success:
        if success==0:
            ingredients_summary.append({'Inredients':[],'Success':0})
        else:
            ingredients_success = [ing for ing in all_ingredients if ing['Success']==success]
            slots_summary = []
            for i in range(ITEM_COUNT):
                slot_i = set([ing['IngIDs'][i] for ing in ingredients_success])
                slot_i_summary = ''
                if len(slot_i) == len(ingredients):
                    slot_i_summary = 'anything, '
                else:
                    if len(ingredients) - len(slot_i) <= cutoff:
                        slot_i_summary = 'anything but '+','.join([ing['Name'] for ing in ingredients if not ing['IngID'] in slot_i])+', '
                    else:
                        for c in category_ingredients:
                            if slot_i & c[1]:
                                if c[1].issubset(slot_i):
                                    slot_i_summary += c[0]
                                else:
                                    if len(slot_i&c[1]) <= cutoff:
                                        slot_i_summary += ','.join([ing['Name'] for ing in ingredients if ing['IngID'] in slot_i&c[1]])
                                    else:
                                        slot_i_summary += (c[0]+' but '+','.join([ing['Name'] for ing in ingredients if ing['IngID'] in c[1]-slot_i]))
                                slot_i_summary += ', '
                slots_summary.append(slot_i_summary[:-2])
            ingredients_summary.append({'Success':success,'Ingredients':slots_summary})
    
    return ingredients_summary

def find_best_recipes_wrap(ingredient_names):
    IngIDs =  [[ing['IngID'] for ing in ingredients if ing['Name']==n][0] for n in ingredient_names]
    return find_best_recipes(IngIDs)

if __name__=='__main__':
    find_all_ingredients_wrap('Dragonpie',['Twigs','Twigs','Monster Meat'])
    find_all_ingredients_wrap('Trail Mix',['Watermelon'])
    find_best_recipes_wrap(['Twigs','Cooked Monster Meat','Roasted Juicy Berries','Juicy Berries', 'Red Cap'])