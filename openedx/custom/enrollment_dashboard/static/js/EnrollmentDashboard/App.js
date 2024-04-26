import logo from './logo.svg';
import React from "react";
import './App.css';
import banner from './assets/header.PNG';
import footer from './assets/footer.PNG';
import {
  Route,
  NavLink,
  HashRouter
} from "react-router-dom";
import Home from "./Home/Home";
import Stuff from "./Primary/Stuff";
import Acknowledgement from "./Acknowledgement/Acknowledgement";
import Details from "./Details/Details";
import Examcard from "./Examcard/Examcard";
import Rawdata from "./RawData/RawData";
import History from "./History/History";
import Academics from "./Academics/Academics";
import MaritalDetails from "./MaritalDetails/MaritalDetails";
import MaritalConfirm from "./MaritalConfirm/MaritalConfirm";
import Personality from "./Personality/Personality";

function App() {
  return (
    <HashRouter>
    <div>
          {/*<div className="banner">*/}
          {/*  <img className="banner-img" src={banner} alt=""></img>*/}
          {/*</div>*/}
          {/* <ul className="header">
          <li><NavLink to="/">Home</NavLink></li>
            <li><NavLink to="/stuff">Stuff</NavLink></li>
            <li><NavLink to="/acknowledgement">Acknowledgement</NavLink></li>
          </ul> */}
          <div className="content">
            <Route exact path="/" component={Home}/>
            <Route path="/stuff" component={Stuff}/>
            <Route path="/acknowledgement" component={Acknowledgement}/>
            <Route path="/details" component={Details}/>
            <Route path="/examcard" component={Examcard}/>
            <Route path="/rawdata" component={Rawdata}/>
            <Route path="/history" component={History}/>
            <Route path="/maritaldetails" component={MaritalDetails}/>
            <Route path="/maritalconfirm" component={MaritalConfirm}/>
            <Route path="/academics" component={Academics}/>
            <Route path="/personality" component={Personality}/>
          </div>
          {/*<div className="footer">*/}
          {/*<img src={footer} alt=""></img>*/}
          {/*</div>*/}
        </div>
    </HashRouter>
  );
}

export default App;
