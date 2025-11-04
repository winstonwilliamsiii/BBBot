import React from 'react';
import ReactDOM from 'react-dom';
import StreamlitComponent from './components/StreamlitComponent';
import './index.css'; // Assuming you have a CSS file for styling

const App = () => {
    return (
        <div>
            <StreamlitComponent />
        </div>
    );
};

ReactDOM.render(<App />, document.getElementById('root'));