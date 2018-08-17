import React from 'react';
import "../css/style.css"
import { FaUtensils } from 'react-icons/fa';

export class Header extends React.Component {
    render() {
        return <h1><FaUtensils /> Recipe Grabber</h1>
    }
}