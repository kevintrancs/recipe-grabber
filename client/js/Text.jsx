import React from 'react';
import "../css/style.css"
import { FaCheck } from 'react-icons/fa';
import 'react-toastify/dist/ReactToastify.css';
import { ToastContainer, toast } from 'react-toastify';

export class Text extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            value: '',
            carrier_value: 'txt.att.net'
        }
        this.handleChange = this.handleChange.bind(this)
        this.sendText = this.sendText.bind(this)
        this.handleChangeCarrier = this.handleChangeCarrier.bind(this)
        this.enterPressed = this.enterPressed.bind(this)
    }

    enterPressed(e){
        if(e.key === 'Enter') { 
            console.log(this.state.carrier_value)
            this.sendText(this.state.value, this.state.carrier_value)
        } 
    }
    handleChange(e) {
        this.setState({ value: e.target.value })
    }
    handleChangeCarrier(e) {
        this.setState({ carrier_value: e.target.value })
    }
    sendText(phone, carrier) {
        console.log(this.state.carrier_value)
        if (phone.trim() != '' && phone.length == 11) {
            this.props.sendText(phone, carrier)
            this.setState({ value: '' })
            toast.success("Sent to Phone!", {
                position: toast.POSITION.TOP_RIGHT
            })
        }
        else{
            toast.error("Please check phone format.", {
                        position: toast.POSITION.TOP_RIGHT
            })
        }
    }
    render() {
        return (
            <div className="form-inline">
                <input type="number" maxLength="10" className="form-control bar-place" value={this.state.value} onKeyPress={this.enterPressed} onChange={this.handleChange} placeholder="ex. 14085551234"></input>
                <button className="button sender" onClick={() => this.sendText(this.state.value, this.state.carrier_value)}><FaCheck /></button>
                <br />
                <select className="form-control bar-place dropdown" value={this.state.carrier_value} onChange={this.handleChangeCarrier} >
                    <option className="item" value="txt.att.net">AT&T</option>
                    <option className="item" value="messaging.sprintpcs.com">Sprint</option>
                    <option className="item" value="tmomail.net">T-Mobile</option>
                    <option className="item" value="vtext.com">Verizon</option>
                    <option className="item" value="sms.mycricket.com">Cricket</option>
                    <option className="item" value="vmobl.com">Virgin</option>
                    <option className="item" value="mymetropcs.com">MetroPCS</option>
                </select>
                <ToastContainer autoClose={1500} />
            </div>
        );
    }
}