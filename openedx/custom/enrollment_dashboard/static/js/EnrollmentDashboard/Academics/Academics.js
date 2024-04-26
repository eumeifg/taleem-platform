import React, { Component } from "react";
import "../../../css/Academics.css";
import { NavLink } from "react-router-dom";

class Academics extends Component {
  render() {
    const options = [
        'الاول الابتدائي​', 'الثالث متوسط​', 'السادس اعدادي​'
      ];
      const defaultOption = options[0];
    return (
        <div className="acadContent">
        <div className="acadMain">
           <div>التحصيل الدراسي​
<br></br>
دروس المرحلة الابتدائية​</div>
        <div className="acadOption">
        <select className="acadDrop" >
          <option>الاول الابتدائي​</option>
          <option>الثالث متوسط​</option>
          <option>السادس اعدادي​</option>
        </select>
        <div className="acadValue">
            <div className="acadIcon">علي محمد احمد​</div>
            <p>اسم الطالب: ​</p>
        </div>
        </div>
        <div>
        <table>
  <tr>
    <th>التاريخ​</th>
    <th>الجغرافية​</th>
    <th>الاجتماعيات​</th>
    <th>العلوم​</th>
    <th>الرياضيات​</th>
    <th>اللغة الانكليزية​</th>
    <th>اللغة العربية​</th>
    <th>التربية الاسلامية​</th>
    <th>المادة الدراسية​</th>
  </tr>
  <tr>
    <td>
        <p>18</p>
        <hr></hr>
        <p>20</p>
    </td>
    <td>
        <p>12</p>
        <hr></hr>
        <p>20</p>
    </td>
    <td>
        <p>16</p>
        <hr></hr>
        <p>20</p>
    </td>
    <td>
        <p>17</p>
        <hr></hr>
        <p>20</p>
    </td>
    <td>
        <p>20</p>
        <hr></hr>
        <p>20</p>
    </td>
    <td>
        <p>18</p>
        <hr></hr>
        <p>20</p>
    </td>
    <td>
        <p>18</p>
        <hr></hr>
        <p>20</p>
    </td>
    <td>
        <p>15</p>
        <hr></hr>
        <p>20</p>
    </td>
    <td>
    الدرجة:​
    </td>
  </tr>
</table>
        <div className="btnline">
        <NavLink className="loginbtnTag" to="/maritalconfirm">رجوع ​</NavLink>
        <NavLink className="loginbtnTag" to="/personality">التالي​</NavLink>
            </div>
        </div>
        </div>
      </div>
    );
  }
}

export default Academics;
