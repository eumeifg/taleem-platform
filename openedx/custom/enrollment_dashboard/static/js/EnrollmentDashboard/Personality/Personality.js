import React, { Component } from "react";
import { NavLink } from "react-router-dom";
import "../../../css/Personality.css";

class Personality extends Component {
  render() {
    return (
        <div className="personalContent">
        <div className="personalMain">
            <p>تقييم الصفات الشخصية للطالب ​</p>
            <table>
                <tr>
                    <th>الاعدادية​
<br></br>3</th>
                    <th>الاعدادية​

<br></br>2</th>
<th>الاعدادية​

<br></br>1</th>
                    <th>
                    المتوسطة​
                    <br></br>3
                    </th>
                    <th>
                    المتوسطة​
                    <br></br>2
                    </th>
                    <th>
                    المتوسطة​
                    <br></br>1
                    </th>
                    <th>
                    الابتدائية
            ​         <br></br>6
                    </th>
                    <th>
                    الابتدائية
            ​         <br></br>5
                    </th>
                    <th>
                    الابتدائية
            ​         <br></br>4
                    </th>
                    <th>
                    الابتدائية
            ​         <br></br>3
                    </th>
                    <th>
                    الابتدائية
            ​         <br></br>2
                    </th>
                    <th>
                    الابتدائية
            ​         <br></br>1
                    </th>
                    <th>السنوات الدراسية​</th>
                </tr>
                <tr>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td>الاتزان ​</td>
                </tr>
                <tr>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td>القيادة​</td>
                </tr>
                <tr>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td>العمل الجماعي​</td>
                </tr>
            </table>
            <div className="btnline">
            <NavLink className="loginbtnTag" to="/academics">رجوع ​</NavLink>
            <NavLink className="loginbtnTag" to="/">التالي​</NavLink>
          </div>
        </div>
      </div>
    );
  }
}

export default Personality;
