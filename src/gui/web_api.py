from flask import Flask, render_template, request
import os
import subprocess
import sys

SCRIPTS = {
    'FINAL': r'/reports/final_estimation.Rmd',
    'MARGINAL': r'/reports/measure_marginal_single.Rmd',
    'ARGUMENTS': r'/reports/measure_arguments_single.Rmd',
}
INPUT_DIR = '/data/'
CURRENT_GAS_COST_PATH = '/reports/current_gas_cost.csv'
OUTPUT_DIR = INPUT_DIR
ALLOWED_ENVS = ['geth', 'erigon', 'ethereumjs', 'nethermind', 'revm', 'besu']


host_output_dir = ""
available_input_paths = []
app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/MARGINAL", methods=["GET", "POST"])
def marginal_report():
    return handle_report('MARGINAL', request)


@app.route("/ARGUMENTS", methods=["GET", "POST"])
def arguments_report():
    return handle_report('ARGUMENTS', request)


@app.route("/FINAL", methods=["GET", "POST"])
def final_report():
    return handle_final_report(request)


def handle_report(report_type, request):
    assert report_type in ['MARGINAL', 'ARGUMENTS']
    # handles GET request to render the initial form
    if request.method == "GET":
        return render_template("report_step1.html", report_type=report_type)
    
    # handles POST requests to render the next form
    else:
        step = request.form.get("step")
        env = request.form.get("env")
        assert env in ALLOWED_ENVS

        if step == "1":
            return render_template("report_step2.html", report_type=report_type, env=env, bytecodes_paths=available_input_paths)
        elif step == "2":
            selected_files = request.form.getlist("selected_bytecodes_paths")
            assert len(selected_files) > 0

            return render_template("report_step3.html", report_type=report_type, env=env, results_paths=available_input_paths, selected_bytecodes_paths=selected_files)
        elif step == "3":
            selected_files = request.form.getlist("selected_bytecodes_paths")
            assert len(selected_files) > 0

            selected_results_paths = request.form.getlist("selected_results_paths")
            assert len(selected_results_paths) > 0

            print(env)
            print(selected_files)
            print(selected_results_paths)

            local_output_file_name = OUTPUT_DIR + selected_files[0] + '_raport_' + report_type + '.html'
            host_output_file_name = host_output_dir + selected_files[0] + '_raport_' + report_type + '.html'
            
            if report_type == 'MARGINAL':
                r_command = f"rmarkdown::render('{SCRIPTS[report_type]}', params=list(env='{env}', programs='{INPUT_DIR + selected_files[0]}', results='{INPUT_DIR + selected_results_paths[0]}', output_estimated_cost='{env}_final_estimated_cost.csv'), output_file='{local_output_file_name}')"
            else:
                r_command = f"rmarkdown::render('{SCRIPTS[report_type]}', params=list(env='{env}', programs='{INPUT_DIR + selected_files[0]}', results='{INPUT_DIR + selected_results_paths[0]}', marginal_estimated_cost='{env}_marginal_estimated_cost.csv', output_estimated_cost='{env}_final_estimated_cost.csv'), output_file='{local_output_file_name}')"
            
            return run_r_script(r_command, host_output_file_name)


def handle_final_report(request):
    if request.method == "GET":
        return render_template("final_report_step_1.html", paths=available_input_paths)
    else:
        paths = request.form.getlist("paths")
        assert len(paths) > 0
        print(paths)

        local_output_file_name = OUTPUT_DIR + 'final_raport.html'
        host_output_file_name = host_output_dir + 'final_raport.html'
        r_command = f"rmarkdown::render('{SCRIPTS['FINAL']}', params=list(estimate_files='{','.join(paths)}', current_gas_cost='{CURRENT_GAS_COST_PATH}'), output_file='{local_output_file_name}')"

        return run_r_script(r_command, host_output_file_name)


def run_r_script(r_command, host_output_file_name):
    print(r_command)
    pro = subprocess.Popen(['Rscript', '-e', r_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    _, stderr = pro.communicate()
    if pro.returncode != 0:
        return render_template("results_error.html", error_message=stderr)

    return render_template("results_success.html", output_file_name=host_output_file_name)


def main():
    global available_input_paths
    global host_output_dir
    host_output_dir = sys.argv[1]

    # Check if the provided path is a directory
    assert os.path.isdir(INPUT_DIR)
        # Get the list of files in the directory
    available_input_paths = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
    print(available_input_paths)
    
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
