import "../css/style.css"
import 'react-toastify/dist/ReactToastify.css';
import React from 'react';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group'
import { ToastContainer, toast } from 'react-toastify';
import { Header } from './Header'
import { RecipeForm } from './RecipeForm'
import { RecipeItem } from './RecipeItem'
import { Text } from './Text'

export class App extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            recipes: []
        }
        this.addRecipe = this.addRecipe.bind(this)
        this.removeRecipes = this.removeRecipes.bind(this)
        this.sendText = this.sendText.bind(this)
    }
    addRecipe(recipe) {
        let recipes = this.state.recipes.slice() //deepcopy this thang
        if(recipe.includes("www") || recipe.includes("//")){
            fetch("http://127.0.0.1:5000/api/scrape?url=" + recipe, {
                method: "GET",
                dataType: "JSON",
                headers: {
                    "Content-Type": "application/json; charset=utf-8",
                }
            })
                .then((resp) => {
                    return resp.json()
                })
                .then((data) => {
                    toast.success("Added Ingrediants!", {
                        position: toast.POSITION.TOP_RIGHT
                    })
                    data.data.forEach(function (entry) {
                        if (!recipes.includes(entry)) {
                            recipes.push({ text: entry })
                        }
                    })
                    this.setState({
                        recipes: recipes
                    })
                })
                .catch((error) => {
                    toast.error("There was a problem with your Link", {
                        position: toast.POSITION.TOP_RIGHT
                    })
                })
        }
        else{
            toast.success("Added Ingrediants!", {
                        position: toast.POSITION.TOP_RIGHT
            })
            recipes.push({text: recipe})
            this.setState({
                recipes: recipes
            })
        }
    }


    sendText(phone, carrier) {
        var items = []
        this.state.recipes.forEach(function (item) {
            items.push(item.text)
        })

        fetch('http://127.0.0.1:5000/api/sendtext', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone: phone,
                items: items,
                carrier: carrier
            })
        })
        .then((resp) => {
            this.setState({
                nextId: 0,
                recipes: []
            })        
        })
        .catch((error)=>{
            toast.error("Please check phone details.",{
                position: toast.POSITION.TOP_RIGHT
            })
        });
    } 

    removeRecipes(id) {
        this.setState({
            recipes: this.state.recipes.filter((recipe, index) => recipe.text !== id)
        });
    }

    render() {
        return (
            <div id="main">
                <Header />
                <RecipeForm addRecipe={this.addRecipe} />
                <br />
                {this.state.recipes.length > 0 ? <Text sendText={this.sendText} /> : null}
                <ul>
                    <ReactCSSTransitionGroup transitionName="anim" transitionAppear={false} transitionEnterTimeout={500} transitionLeaveTimeout={500} transitionEnter={true} transitionLeave={true}>
                        {this.state.recipes.map((recipe) => {
                            return <RecipeItem recipe={recipe} key={recipe.text} id={recipe.text} removeRecipes={this.removeRecipes} />
                        })}
                    </ReactCSSTransitionGroup>
                </ul>
                <ToastContainer autoClose={1500} />
            </div>
        )
    }
}