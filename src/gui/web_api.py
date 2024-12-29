from flask import Flask, render_template, request
import os
import subprocess

SCRIPTS = {
    'FINAL': r'/reports/final_estimation.Rmd',
    'MARGINAL': r'/reports/measure_marginal_single.Rmd',
    'ARGUMENTS': r'/reports/measure_arguments_single.Rmd',
}
INPUT_DIR = '/data/'


available_input_paths = []
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        step = request.form.get("step")
        print(step)

        if step == "1":
            env = request.form.get("env")
            raport_type = request.form.get("raport_type")
            # No need to initialize selected_file_paths here
            return render_template("step2.html", env=env, raport_type = raport_type, bytecodes_paths=available_input_paths)
        elif step == "2":
            # Initialize selected_file_paths for step 2
            selected_bytecodes_paths = request.form.getlist("selected_bytecodes_paths")
            print(selected_bytecodes_paths)
            env = request.form.get("env")
            raport_type = request.form.get("raport_type")
            return render_template("step3.html", env=env, results_paths=available_input_paths, selected_bytecodes_paths=selected_bytecodes_paths, raport_type = raport_type)
        elif step == "3":
            # Initialize selected_final_file_paths for step 3
            env = request.form.get("env")
            raport_type = request.form.get("raport_type")
            selected_bytecodes_paths = request.form.getlist("selected_bytecodes_paths")
            assert len(selected_bytecodes_paths) > 0

            selected_results_paths = request.form.getlist("selected_results_paths")
            assert len(selected_results_paths) > 0

            print(env)
            print(raport_type)
            print(selected_bytecodes_paths)
            print(selected_results_paths)
            
            r_command = f"rmarkdown::render('{SCRIPTS[raport_type]}', params=list(env='geth', programs='{INPUT_DIR + selected_bytecodes_paths[0]}', results='{INPUT_DIR + selected_results_paths[0]}', output_estimated_cost='erigon_marginal_estimated_cost.csv'), output_file='{INPUT_DIR + selected_bytecodes_paths[0] + '_raport.html'}')"
            print(r_command)

            #most likely wrong path, because it maps to host, web_api.py should be copied into the container
            invocation = ['Rscript', '-e', r_command]
            
            pro = subprocess.Popen(invocation, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = pro.communicate()
            print(stdout)
            print(stderr)

            return render_template("results.html", env=env, raport_type=raport_type)

    return render_template("step1.html")


def main():
    # Check if the command line argument is provided
    global available_input_paths

    # Check if the provided path is a directory
    assert os.path.isdir(INPUT_DIR)
        # Get the list of files in the directory
    available_input_paths = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    print(available_input_paths)
    
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
