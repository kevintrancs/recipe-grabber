import "../css/style.css"
import React from 'react';
import { FaTrashAlt } from 'react-icons/fa';

export class RecipeItem extends React.Component {
    constructor(props) {
        super(props)
    }

    removeRecipes(id) {
        this.props.removeRecipes(id)
    }

    render() {
        return (
            <div>
                <li className="swing">
                    <span className="recipe-text">{this.props.recipe.text}</span>
                    <button className="remove-btn" onClick={(e) => this.removeRecipes(this.props.id)}> <FaTrashAlt /></button
                    ></li>
            </div>
        );
    }
}