#include <scitbx/array_family/boost_python/flex_wrapper.h>
#include <scitbx/array_family/versa_matrix.h>
#include <scitbx/matrix/outer_product.h>
#include <scitbx/matrix/norms.h>
#include <scitbx/matrix/move.h>
#include <boost/python/args.hpp>
#include <boost/python/overloads.hpp>
#include <boost/python/return_value_policy.hpp>
#include <boost/python/return_by_value.hpp>
#include <boost_adaptbx/std_pair_conversion.h>

namespace scitbx { namespace af {

namespace {

  // test here in lack of a better place
  void
  exercise_packed_u_accessor()
  {
    versa<double, matrix::packed_u_accessor>
      a(matrix::packed_u_accessor(5));
    ref<double, matrix::packed_u_accessor> r = a.ref();
    SCITBX_ASSERT(a.size() == 5*(5+1)/2);
    SCITBX_ASSERT(r.size() == 5*(5+1)/2);
    SCITBX_ASSERT(a.accessor().n == 5);
    SCITBX_ASSERT(r.accessor().n == 5);
    for(unsigned i=0;i<r.size();i++) r[i] = i+1;
    unsigned v = 1;
    for(unsigned i=0;i<r.accessor().n;i++) {
      for(unsigned j=i;j<r.accessor().n;j++,v++) {
        SCITBX_ASSERT(a(i,j) == v);
        SCITBX_ASSERT(r(i,j) == v);
      }
    }
  }

  bool
  is_square_matrix(
    versa<double, flex_grid<> > const& self)
  {
    return self.accessor().is_square_matrix();
  }

} // namespace <anonymous>

namespace boost_python {

  versa<double, c_grid<2> >
  matrix_multiply_real_matrix_real_matrix(
    const_ref<double, c_grid<2> > const& a,
    const_ref<double, c_grid<2> > const& b)
  {
    return matrix_multiply(a, b);
  }

  versa<std::complex<double>, c_grid<2> >
  matrix_multiply_real_matrix_complex_matrix(
    const_ref<double, c_grid<2> > const& a,
    const_ref<std::complex<double>, c_grid<2> > const& b)
  {
    return matrix_multiply(a, b);
  }

  versa<double, c_grid<2> >
  matrix_multiply_packed_u_real_matrix_real_u(
    const_ref<double, c_grid<2> > const& a,
    const_ref<double> const& b)
  {
    return matrix_multiply_packed_u(a, b);
  }

  versa<std::complex<double>, c_grid<2> >
  matrix_multiply_packed_u_real_matrix_complex_u(
    const_ref<double, c_grid<2> > const& a,
    const_ref<std::complex<double> > const& b)
  {
    return matrix_multiply_packed_u(a, b);
  }

  shared<double>
  matrix_multiply_packed_u_multiply_lhs_transpose_real_matrix_real_u(
    const_ref<double, c_grid<2> > const& a,
    const_ref<double> const& b)
  {
    return matrix_multiply_packed_u_multiply_lhs_transpose(a, b);
  }

  shared<std::complex<double> >
  matrix_multiply_packed_u_multiply_lhs_transpose_real_matrix_complex_u(
    const_ref<double, c_grid<2> > const& a,
    const_ref<std::complex<double> > const& b)
  {
    return matrix_multiply_packed_u_multiply_lhs_transpose(a, b);
  }

  BOOST_PYTHON_FUNCTION_OVERLOADS(
    matrix_symmetric_as_packed_u_overloads,
    matrix::symmetric_as_packed_u, 1, 2)
  BOOST_PYTHON_FUNCTION_OVERLOADS(
    matrix_symmetric_as_packed_l_overloads,
    matrix::symmetric_as_packed_l, 1, 2)

  double (*matrix_norm_1)(const_ref<double, mat_grid> const &) = matrix::norm_1;

  void
  wrap_flex_double_matrix(
    flex_wrapper<double>::class_f_t& class_f_t)
  {
    exercise_packed_u_accessor();

    using namespace boost::python;

    boost_adaptbx::std_pair_conversions::to_tuple<shared<double>,
                                                  shared<double> >();

    class_f_t
      .def("is_square_matrix", is_square_matrix)
      .def("matrix_diagonal",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&)) matrix_diagonal)
      .def("matrix_upper_bidiagonal", matrix_upper_bidiagonal<double>)
      .def("matrix_lower_bidiagonal", matrix_lower_bidiagonal<double>)
      .def("matrix_diagonal_set_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&,
          double const&)) matrix_diagonal_set_in_place,
            arg_("value"))
      .def("matrix_diagonal_set_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&,
          const_ref<double> const&)) matrix_diagonal_set_in_place,
            arg_("diagonal"))
      .def("matrix_diagonal_add_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&,
          double const&)) matrix_diagonal_add_in_place,
            arg_("value"))
      .def("matrix_diagonal_sum",
        (double(*)(
          const_ref<double, c_grid<2> > const&)) matrix_diagonal_sum)
      .def("matrix_trace",
        (double(*)(
          const_ref<double, c_grid<2> > const&)) matrix_diagonal_sum)
      .def("matrix_diagonal_product",
        (double(*)(
          const_ref<double, c_grid<2> > const&)) matrix_diagonal_product)
      .def("matrix_norm_1", matrix_norm_1)
      .def("matrix_norm_inf", matrix::norm_inf<double>)
      .def("matrix_norm_frobenius", matrix::norm_frobenius<double>)
      .def("matrix_multiply", matrix_multiply_real_matrix_real_matrix)
      .def("matrix_multiply", matrix_multiply_real_matrix_complex_matrix)
      .def("matrix_multiply",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&,
          const_ref<double> const&)) matrix_multiply)
      .def("matrix_multiply",
        (shared<double>(*)(
          const_ref<double> const&,
          const_ref<double, c_grid<2> > const&)) matrix_multiply)
      .def("matrix_multiply",
        (double(*)(
          const_ref<double> const&,
          const_ref<double> const&)) matrix_multiply)
      .def("dot",
        (double(*)(
          const_ref<double> const&,
          const_ref<double> const&)) matrix_multiply)
      .def("matrix_multiply_packed_u",
        matrix_multiply_packed_u_real_matrix_real_u)
      .def("matrix_multiply_packed_u",
        matrix_multiply_packed_u_real_matrix_complex_u)
      .def("matrix_multiply_packed_u_multiply_lhs_transpose",
        matrix_multiply_packed_u_multiply_lhs_transpose_real_matrix_real_u, (
          arg_("packed_u")))
      .def("matrix_multiply_packed_u_multiply_lhs_transpose",
        matrix_multiply_packed_u_multiply_lhs_transpose_real_matrix_complex_u,(
          arg_("packed_u")))
      .def("matrix_transpose_multiply_as_packed_u",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&))
            matrix_transpose_multiply_as_packed_u)
      .def("matrix_transpose_multiply_diagonal_multiply_as_packed_u",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&,
          const_ref<double> const&))
            matrix_transpose_multiply_diagonal_multiply_as_packed_u, (
              arg_("diagonal_elements")))
      .def("matrix_transpose",
        (versa<double, c_grid<2> >(*)(
           const_ref<double, c_grid<2> > const&)) matrix_transpose)
      .def("matrix_transpose_in_place",
        (void(*)(versa<double, flex_grid<> >&)) matrix_transpose_in_place)
      .def("matrix_outer_product",
        (versa<double, c_grid<2> >(*)(
           const_ref<double> const&,
           const_ref<double> const&)) matrix::outer_product, (arg_("rhs")))
      .def("matrix_lu_decomposition_in_place",
        (shared<std::size_t>(*)(
          ref<double, c_grid<2> > const&)) matrix_lu_decomposition_in_place)
      .def("matrix_lu_back_substitution",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&,
          const_ref<std::size_t> const&,
          const_ref<double> const&)) matrix_lu_back_substitution, (
        arg_("pivot_indices"), arg_("b")))
      .def("matrix_forward_substitution", matrix_forward_substitution<double>,
           (arg_("l"), arg_("b"), arg_("unit_diag")=false))
      .def("matrix_back_substitution", matrix_back_substitution<double>,
           (arg_("u"), arg_("b"), arg_("unit_diag")=false))
      .def("matrix_forward_substitution_given_transpose",
           matrix_forward_substitution_given_transpose<double>,
           (arg_("u"), arg_("b"), arg_("unit_diag")=false))
      .def("matrix_back_substitution_given_transpose",
           matrix_back_substitution_given_transpose<double>,
           (arg_("l"), arg_("b"), arg_("unit_diag")=false))
      .def("matrix_determinant_via_lu",
        (double(*)(
          const_ref<double, c_grid<2> > const&,
          const_ref<std::size_t> const&)) matrix_determinant_via_lu, (
        arg_("pivot_indices")))
      .def("matrix_determinant_via_lu",
        (double(*)(
          const_ref<double, c_grid<2> > const&)) matrix_determinant_via_lu)
      .def("matrix_inversion_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&,
          ref<double, c_grid<2> > const&)) matrix_inversion_in_place, (
        arg_("b")))
      .def("matrix_inversion_in_place",
        (void(*)(ref<double, c_grid<2> > const&)) matrix_inversion_in_place)
      .def("matrix_upper_triangle_as_packed_u",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&))
            matrix::upper_triangle_as_packed_u)
      .def("matrix_packed_u_as_upper_triangle",
        (versa<double, c_grid<2> >(*)(
          const_ref<double> const&))
            matrix::packed_u_as_upper_triangle)
      .def("matrix_lower_triangle_as_packed_l",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&))
            matrix::lower_triangle_as_packed_l)
      .def("matrix_packed_l_as_lower_triangle",
        (versa<double, c_grid<2> >(*)(
          const_ref<double> const&))
            matrix::packed_l_as_lower_triangle)
      .def("matrix_symmetric_as_packed_u",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&, double const&))
            matrix::symmetric_as_packed_u,
              matrix_symmetric_as_packed_u_overloads((
                arg_("self"),
                arg_("relative_epsilon")=1.e-12)))
      .def("matrix_symmetric_as_packed_l",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&, double const&))
            matrix::symmetric_as_packed_l,
              matrix_symmetric_as_packed_l_overloads((
                arg_("self"),
                arg_("relative_epsilon")=1.e-12)))
      .def("matrix_is_symmetric",
        (bool(*)(
          const_ref<double, c_grid<2> > const&, double const&))
            matrix::is_symmetric, ((
              arg_("self"),
              arg_("relative_epsilon"))))
      .def("matrix_packed_u_as_symmetric",
        (versa<double, c_grid<2> >(*)(
          const_ref<double> const&))
            matrix::packed_u_as_symmetric)
      .def("matrix_packed_l_as_symmetric",
        (versa<double, c_grid<2> >(*)(
          const_ref<double> const&))
            matrix::packed_l_as_symmetric)
      .def("matrix_packed_u_diagonal",
        (shared<double>(*)(
          const_ref<double> const&))
            matrix::packed_u_diagonal)
      .def("matrix_copy_upper_to_lower_triangle_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&))
            matrix::copy_upper_to_lower_triangle_in_place)
      .def("matrix_copy_lower_to_upper_triangle_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&))
            matrix::copy_lower_to_upper_triangle_in_place)
      .def("matrix_copy_column",
        (shared<double>(*)(
          const_ref<double, c_grid<2> > const&,
          unsigned))
            matrix::copy_column, (
              arg_("i_column")))
      .def("matrix_copy_block",
        (versa<double, c_grid<2> >(*)(
          const_ref<double, c_grid<2> > const&,
          unsigned, unsigned, unsigned, unsigned))
            matrix::copy_block, (
              arg_("i_row"),
              arg_("i_column"),
              arg_("n_rows"),
              arg_("n_columns")))
      .def("matrix_paste_block_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&,
          const_ref<double, c_grid<2> > const&,
          unsigned, unsigned))
            matrix::paste_block_in_place, (
              arg_("block"),
              arg_("i_row"),
              arg_("i_column")))
      .def("matrix_copy_upper_triangle", matrix::copy_upper_triangle<double>)
      .def("matrix_copy_lower_triangle", matrix::copy_lower_triangle<double>)
      .def("matrix_swap_rows_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&, unsigned, unsigned))
            matrix::swap_rows_in_place, (
                arg_("self"),
                arg_("i"),
                arg_("j")))
      .def("matrix_swap_columns_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&, unsigned, unsigned))
            matrix::swap_columns_in_place, (
                arg_("self"),
                arg_("i"),
                arg_("j")))
      .def("matrix_symmetric_upper_triangle_swap_rows_and_columns_in_place",
        (void(*)(
          ref<double, c_grid<2> > const&, unsigned, unsigned))
            matrix::symmetric_upper_triangle_swap_rows_and_columns_in_place, (
                arg_("self"),
                arg_("i"),
                arg_("j")))
      .def("matrix_packed_u_swap_rows_and_columns_in_place",
        (void(*)(
          ref<double> const&, unsigned, unsigned))
            matrix::packed_u_swap_rows_and_columns_in_place, (
                arg_("self"),
                arg_("i"),
                arg_("j")))
      .def("cos_angle",
        (boost::optional<double>(*)(
          const_ref<double> const&,
          const_ref<double> const&)) cos_angle, (
        arg_("b")))
      .def("cos_angle",
        (double(*)(
          const_ref<double> const&,
          const_ref<double> const&,
          const double&)) cos_angle, (
        arg_("b"), arg_("value_if_undefined")))
      .def("angle",
        (boost::optional<double>(*)(
          const_ref<double> const&,
          const_ref<double> const&)) angle, (
        arg_("b")))
      .def("angle",
        (boost::optional<double>(*)(
          const_ref<double> const&,
          const_ref<double> const&,
          bool)) angle, (
        arg_("b"), arg_("deg")=false))
    ;
  }

}}} // namespace scitbx::af::boost_python
