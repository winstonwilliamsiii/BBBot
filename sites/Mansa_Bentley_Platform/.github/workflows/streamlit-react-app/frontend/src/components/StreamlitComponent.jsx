import React from 'react';

const StreamlitComponent = () => {
    const [data, setData] = React.useState(null);

    React.useEffect(() => {
        // Fetch data from the Streamlit backend
        const fetchData = async () => {
            const response = await fetch('/api/data');
            const result = await response.json();
            setData(result);
        };

        fetchData();
    }, []);

    return (
        <div style={{ backgroundColor: '#f0f0f0', color: '#333', padding: '20px' }}>
            <h1>Streamlit Data</h1>
            {data ? (
                <pre>{JSON.stringify(data, null, 2)}</pre>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
};

export default StreamlitComponent;