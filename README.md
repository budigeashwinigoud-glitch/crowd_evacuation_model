# Crowd Evacuation Modeling and Simulation Using Python

## 1. Project Title
Crowd Evacuation Modeling and Simulation Using Python

## 2. Problem Statement
Emergency evacuation is a classic problem in applied mathematics and engineering. In a building, people move toward available exits while interacting with local crowd density and obstacles. A good model must describe the motion of each person, estimate crowd density, and compare numerical approaches such as Euler and RK4. This project studies how evacuation depends on density, exit placement, and the numerical method used to solve the motion equations.

## 3. Objectives
- Mathematical modeling of crowd movement
- Differential equations for position and velocity
- Distance and direction calculation toward exits
- Density calculation across grid cells
- Density-dependent speed calculation
- Numerical simulation using Euler and RK4 methods
- Visualization of evacuation and density patterns
- Web-based prototype interface for local simulation testing

## 4. Mathematical Model
The project models each person as a moving particle in a 2D building.

### Differential Equations
$$
\frac{dx}{dt} = v_x, \quad \frac{dy}{dt} = v_y
$$

### Distance to Exit
$$
d = \sqrt{(x_e - x)^2 + (y_e - y)^2}
$$

### Direction Vector and Normalization
$$
D = (x_e - x, y_e - y), \quad \hat{D} = \frac{D}{\|D\|}
$$

### Crowd Density
$$
\rho = \frac{N}{A}
$$

### Density-dependent Speed
$$
v(\rho) = v_0\left(1 - \frac{\rho}{\rho_{max}}\right)
$$

### Euler Method
$$
x_{n+1} = x_n + \Delta t \, v_x
$$
$$
y_{n+1} = y_n + \Delta t \, v_y
$$

### RK4 Method
Runge-Kutta 4th-order is also used to update the state more accurately across the same time step.

## 5. System Architecture
The project uses both a command-line simulation and a browser-based prototype.

Frontend → Flask API → Python Simulation Engine → Mathematical Models → Results

### Key files
- `main.py`: command-line simulation menu
- `config.py`: global simulation parameters
- `models/`: person, building, and exit definitions
- `mathematics/`: distance, density, velocity, differential equations, and numerical methods
- `simulation/`: scenario generation and simulation engine
- `visualization/`: charts, heatmaps, and animation generation
- `backend/app.py`: Flask server
- `backend/routes.py`: REST API endpoints
- `frontend/index.html`: web dashboard layout
- `frontend/style.css`: dashboard styling
- `frontend/script.js`: API calls and chart rendering
- `results/`: CSV and image outputs

## 6. Installation
Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install the project requirements:

```bash
pip install -r requirements.txt
```

## 7. How to Run
### CLI mode
```bash
python main.py
```

### Web prototype mode
```bash
python backend/app.py
```
Then open the browser at:

```text
http://localhost:5000/
```

## 8. Experiments
The project includes:
1. Normal Evacuation
2. High Crowd
3. Blocked Exit
4. Three Exits
5. Different Exit Locations
6. Euler vs RK4 comparison

## 9. Results and Visualization
The project produces:
- CSV simulation summaries
- evacuation curves
- density heatmaps
- exit utilization charts
- browser-based dashboard metrics

## 10. Limitations
This is a simplified mathematical model and does not represent every real-world human behavior. It is designed for educational and prototype demonstration purposes.

## 11. Future Improvements
- social-force model
- dynamic obstacles
- multi-floor simulation
- realistic building layouts
- more advanced crowd-flow equations

## 12. Mathematical File Mapping
- Differential equations: `mathematics/differential_equation.py`
- Distance calculation: `mathematics/distance.py`
- Density calculation: `mathematics/density.py`
- Velocity calculation: `mathematics/velocity.py`
- Euler and RK4 method: `mathematics/numerical_methods.py`
- Simulation logic: `simulation/crowd_simulator.py`
- Scenario setup: `simulation/scenarios.py`
- API layer: `backend/routes.py`
- Frontend dashboard: `frontend/index.html`

## 13. API Endpoints
- `GET /api/health`
- `GET /api/scenarios`
- `POST /api/simulate`
- `GET /api/results`
- `GET /api/results/csv`

## 14. Academic Note
This project keeps the mathematical engine as the core implementation, while the Flask and frontend layers act as a prototype interface for demonstration in a local VS Code environment.
