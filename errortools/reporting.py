import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import scipy

def show_parabolic_approximation(model, n_points=21, n_stddevs=1, pdf=None):
    """
    Calculates the loss function and its parabolic approximation around the
    fitted minimum in all of the parameters

    The parabolic approximation is of the loss function is often made to estimate
    parameter errors. The accuracy of the errors depends on the closeness of the
    approximation

    :param model: fitted model. Needs to expose
        a loss method to calculate the loss,
        a parameters attribute to get the fitted parameter values,
        X and y attributes to get the training features and targets,
        a hessian_mtx attribute or cvr_mtx attribute to determine the
            hessian at the minimum
        an errors attribute or cvr_mtx attribute to determine the
            errors of the parameters
    :param n_points: [int] number of points in each of the parameters
        to calculate loss and parabolic approximation on
    :param n_stddevs: [float] number of times the error on a parameter
        left and right of the minimum to calculate loss an approximation on
    :param pdf: [PdfPages, str, or None] If instance of PdfPages plots will
        be added to the pdf. If str a new pdf will be created by this name.
    :return: PdfPages if pdf is not None, else three numpy 2D arrays
        parameter values, loss function values, parabolic approximation values
        of shape (n_parameters, n_points,)
    """
    # ToDo add gradient of loss
    if not hasattr(model, "loss"):
        raise ValueError("Expect model to have a loss function")
    else:
        loss_fnc = model.loss

    if not hasattr(model, "parameters"):
        raise ValueError("Expect model to expose parameters")
    else:
        parameters0 = model.parameters

    if parameters0.shape[0] == 0:
        raise RuntimeError("No parameters, nothing to report")

    if not hasattr(model, 'X') or not hasattr(model, 'y'):
        raise ValueError("Expect model to expose training features X and targets y")
    else:
        X = model.X
        y = model.y

    if not hasattr(model, "hessian_mtx"):
        if not hasattr(model, "cvr_mtx"):
            raise ValueError("For a parabolic approximation expect model to expose a covariance matrix")
        else:
            hessian_mtx = scipy.linalg.inv(model.cvr_mtx)
    else:
        hessian_mtx = model.hessian_mtx

    if not hasattr(model, "errors"):
        if not hasattr(model, 'cvr_mtx'):
            raise ValueError("Expect model to expose errors or a covariance matrix")
        else:
            errors = np.sqrt(np.diag(model.cvr_mtx))
    else:
        errors = model.errors

    if isinstance(pdf, PdfPages):
        pass
    elif isinstance(pdf, str):
        pdf = PdfPages(pdf)

    f0 = loss_fnc(parameters0, X, y)

    if pdf is None:
        axes = np.empty((parameters0.shape[0], n_points), dtype=float)
        losses = np.empty((parameters0.shape[0], n_points), dtype=float)
        parabolics = np.empty((parameters0.shape[0], n_points), dtype=float)
    else:
        n_cols = min(4, parameters0.shape[0])
        n_rows = min(10, parameters0.shape[0]//n_cols + int(parameters0.shape[0]%n_cols > 0))
        fig = plt.subplots(n_rows, n_cols, figisize=(n_rows*4, n_cols*4))
        i_row = i_col = 0

    p_tiled = np.tile(parameters0, n_points).reshape((n_points, -1))
    for i in range(parameters0.shape[0]):
        p = p_tiled.copy()
        p[:,i] = p[:,i] + np.linspace(-n_stddevs*errors[i], n_stddevs*errors[i], n_points, endpoint=True)
        f = np.array([loss_fnc(u, X, y) for u in p])
        g = np.array([f0 + 0.5*np.dot(u-parameters0, np.dot(hessian_mtx, u-parameters0)) for u in p])
        if pdf is None:
            axes[i] = p[:,i]
            losses[i] = f
            parabolics[i] = g
        if pdf is not None:
            ax[i_row, i_col].plot(p[:, i], f, '-', color='orange', label="loss function")
            ax[i_row, i_col].plot(p[:, i], g, '--', color='red', label="parabolic approximation")
            i_col += 1
            if i_col == n_cols:
                i_row += 1
                i_col = 0
                if i_row == n_rows:
                    pdf.savefig(fig)
                    fig, ax = plt.subplots(n_rows, n_cols, figisize=(n_rows*4, n_cols*4))
                    i_row = 0
    if pdf is None:
        return axes, losses, parabolics
    else:
        if i_row != 0 or i_col != 0:
            pdf.savefig(fig)
        return pdf