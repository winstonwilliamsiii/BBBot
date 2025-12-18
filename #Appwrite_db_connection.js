// Appwrite Database Connection

const sdk = require('node-appwrite');

// Init SDK
const client = new sdk.Client();
const tablesDB = new sdk.TablesDB(client);

client
    .setEndpoint('https://<REGION>.cloud.appwrite.io/v1') // Your API Endpoint
    .setProject('<PROJECT_ID>') // Your project ID
    .setKey('<API_KEY>'); // Your secret API key

// Create a table for `team_members` junction table
const createTeamMembersTable = tablesDB.create({
    databaseId: '<DATABASE_ID>',
    name: 'team_members',
    attributes: [
        { key: 'team_id', type: 'string', required: true },
        { key: 'user_id', type: 'string', required: true }
    ],
    indexes: [
        { key: 'primary', type: 'primary', attributes: ['team_id', 'user_id'] }
    ]
});

createTeamMembersTable.then(function (response) {
    console.log('Team Members Table Created:', response);
}, function (error) {
    console.error('Error Creating Team Members Table:', error);
});

// Add indexes to existing tables
const updateIndexes = tablesDB.update({
    databaseId: '<DATABASE_ID>',
    tableId: '<TABLE_ID>',
    indexes: [
        { key: 'idx_user_id', type: 'key', attributes: ['user_id'] },
        { key: 'idx_symbol_date', type: 'key', attributes: ['symbol', 'date'] }
    ]
});

updateIndexes.then(function (response) {
    console.log('Indexes Updated:', response);
}, function (error) {
    console.error('Error Updating Indexes:', error);
});

// Create a table for `transactions` in `mydb` schema
const createTransactionsTable = tablesDB.create({
    databaseId: '<DATABASE_ID>',
    name: 'transactions',
    attributes: [
        { key: 'transaction_id', type: 'string', required: true },
        { key: 'user_id', type: 'string', required: true },
        { key: 'amount', type: 'float', required: true },
        { key: 'date', type: 'datetime', required: true },
        { key: 'created_at', type: 'datetime', required: true },
        { key: 'updated_at', type: 'datetime', required: true }
    ],
    indexes: [
        { key: 'idx_user_id', type: 'key', attributes: ['user_id'] },
        { key: 'idx_date', type: 'key', attributes: ['date'] }
    ]
});

createTransactionsTable.then(function (response) {
    console.log('Transactions Table Created:', response);
}, function (error) {
    console.error('Error Creating Transactions Table:', error);
});
