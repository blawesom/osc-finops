osc-finops requirements

we want to design a service for outscale customers and users as a finops tool for project manager, cfo,  accountants and outscale customer team.

this service should support at least these functions:

1/ build a quote based on resources and region catalog prices like cockpit-ext
2/ get history of consumption, with granularity option (per day, week or month) (like osc-draft-invoicing)
3/ evaluate current cost of used resources (like osc-cost)
4/ analyse trend of resources usage and cost drift based on a defined budget or plan (like osc-cost)

The service should be composed of atomic functions based on a REST python backend and a html/css/js frontend.

backend will have different function to allow queries to the api with customer credentials provided at login by the user and safely stored for the duration of the session
api calls will be authenticated with documented signature methods and will preferably use existing sdks

internal services will be in charge of correlating usage, plan and prices

front end should be as simple as possible with different tabs based on customer workflows. styling should stay aligned with existing reference project such as cockcpit-ext

start project by defining architecture document, gitignore, readme and test scenarios.

then write an extensive Product Requirement Document for this service, and main tasks content that would allow a team of developpers to start working on this project.