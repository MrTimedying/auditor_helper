# Ideas implementation


1. Settings for week duration
    1.1 Setting that allows to set a custom week duration from a specific hour and day of the week to another;
    1.2 This will store in memory and influence the way weeks are added in the week_widget (it will allow to add new weeks without having to input start and end time);
    1.3 The actual way to add new weeks will be the custom way, whilst the automatic way will take account of the last week and add a new one based on current time and the saved standard week duration;
    1.4 Limited use case feature: if a user is adding a task that has a time_begin beyond the ranges of the current week the app will toast "You're beyond the range of this week, want to add this task to the new week?" and the user will also have the possibility to accept or decline and add it to the current week regardless;

2. Settings for weekly bonus (affects the payrate)
    2.1 Possiblity to configure in the settings the weekly bonus reward;
    2.2 The configurator will allow to configure start and end time for the bonus;
    2.3 Other potential bonus features (for example, a specific amount of money that will be given after a specific amount of task completed in that specific timeframe of the bonus window);
    2.4 Potentially in this case removing the checkbox for manual tag of the bonus paid task;
    2.5 The bonus week setting won't be in the settings menu, but will be an adhoc option that can be set up in the data_grid;
    2.6 The task data that is stored will potentially also be a boolean (true/false) for bonus truthfulness or not in the db for the specific task, but the data analysis will be handled differently because it has to incorporate all the time window, and additional data in the options for the specific week that is tagged as a bonus week;

3. Adding special rows which are called OH or office hours
    3.1 These rows will respect the schema, the only difference is that they will at the Operation ID another code set up that is a pin, which is shown as hidden like a password;
    3.2 The rows attempt ID will be SHOWN black or with a placeholder, but the data that will be sent to DB is a dummy generated code;
    3.3 Project Name will be office hours;
    3.4 Duration will be 30 minutes flat, already set (in case of another 30 minutes of office hours, another special task entry can be added);
    3.5 Manually set in this case will be also start time and end time;
    
