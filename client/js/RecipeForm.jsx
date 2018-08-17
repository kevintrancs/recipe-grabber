import React from 'react';
import "../css/style.css"
import { FaSearch } from 'react-icons/fa';
import 'react-toastify/dist/ReactToastify.css';
import { ToastContainer, toast } from 'react-toastify';

export class RecipeForm extends React.Component {
    constructor(props) {
        super(props)
        this.state = { value: '' }
        this.handleChange = this.handleChange.bind(this)
        this.addRecipe = this.addRecipe.bind(this)
        this.enterPressed = this.enterPressed.bind(this)
    }

    handleChange(e) {
        this.setState({ value: e.target.value })
    }
    
    enterPressed(e){
        if(e.key === 'Enter') { 
            this.addRecipe(this.state.value)
        } 
    }

    addRecipe(recipe) {
        if (recipe.trim() != '' && recipe.length > 0) {
            this.props.addRecipe(recipe)
            this.setState({ value: '' })
        }
        else{
            toast.error("Please enter an item/link", {
                        position: toast.POSITION.TOP_RIGHT
            })
        }
    }
    render() {
        return (
            <div className="form-inline">
                <input type="text" className="form-control bar-place" value={this.state.value} onChange={this.handleChange} onKeyPress={this.enterPressed.bind(this)} placeholder="URL or Item name"></input>
                <button className="search" onClick={() => this.addRecipe(this.state.value)}><FaSearch /></button>
                <ToastContainer autoClose={1500} />
            </div>
        );
    }
}