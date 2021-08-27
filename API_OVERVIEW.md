# APIs in Tisane

There are four main categories of APIs in Tisane:

 - Data variable creators
 - Data variable relationship adders
 - Study design
 - Inference functions

# Data Variables

## tisane.Unit

### Initialization
```python
tisane.Unit(self, name, data=None, cardinality=None, **kwargs)
```

A data variable that can have attributes. For example, if you have people in your dataset, and each person has an eye color, height, age, etc., then you should make the person variable a `Unit`.

Parameters:

 - `name: str` -- the name of the variable. If you have data, this should correspond to the column's name.
 - `data: tisane.data.DataVector` --
 - `cardinality: int` -- the number of unique instances of the variable. For example, if there are 100 participants in the study, even if you have multiple data points from each participant, you specify `cardinality=100`.
 - `kwargs` --

### tisane.Unit.nominal
```python
tisane.Unit.nominal(self, name, data=None, number_of_instances=1, **kwargs)
```

Creates a categorical data variable that is an attribute of a `tisane.Unit`.

Parameters:

 - `name: str` -- the name of the variable. If you have data, this should correspond to the column's name.
 - `data: tisane.data.DataVector` --
 - `number_of_instances` -- either an `int`, `tisane.AbstractVariable`, or `tisane.variable.AtMost`. Defaults to `1`. This should be the number of measurements of an attribute per unique instance of the associated `tisane.Unit`. For example, if you measure the reaction time of a person 10 times, then you should enter 10.
 - `kwargs` --

Returns: A `tisane.variable.Nominal` object

### tisane.Unit.ordinal
```python
tisane.Unit.ordinal(self, name, order, cardinality=None, data=None, number_of_instances=1)
```

Creates a categorical data variable whose categories are ordered. For example, this could be used to represent age ranges: <18, 18-30, 31-45, 46-65, 65+. There is an ordering to these categories. Another example are specific treatments in a study, such as giving pigs 0 mg of copper, 35 mg of copper, or 175 mg of copper.

Parameters:

- `name: str` -- the name of the variable. If you have data, this should correspond to the column's name.
- `order: list` -- a list of the categories, in the order desired
- `cardinality: int` -- the number of unique instances of the variable
- `data: tisane.data.DataVector` --
- `number_of_instances` -- either an `int`, `tisane.AbstractVariable`, or `tisane.variable.AtMost`. Defaults to `1`. This should be the number of measurements of an attribute per unique instance of the associated `tisane.Unit`. For example, if you measure the reaction time of a person 10 times, then you should enter 10.
- `kwargs` --

Returns: `tisane.variable.Ordinal`, the `Ordinal` data variable

### tisane.Unit.numeric
```python
tisane.Unit.numeric(self, name, data=None, number_of_instances=1)
```

Creates a variable that can be either a float or an integer. The range is not constrained.

Parameters:

- `name: str` -- the name of the variable. If you have data, this should correspond to the column's name.
- `data: tisane.data.DataVector` --
- `number_of_instances` -- either an `int`, `tisane.AbstractVariable`, or `tisane.variable.AtMost`. Defaults to `1`. This should be the number of measurements of an attribute per unique instance of the associated `tisane.Unit`. For example, if you measure the reaction time of a person 10 times, then you should enter 10.

Returns: `tisane.variable.Numeric`, the `Numeric` data variable

### tisane.Unit.nests_within
```python
tisane.Unit.nests_within(self, group)
```

Adds a nests-in relationship to the associated `tisane.Unit`. For example, if you have units `students` and `schools`, then you can add the nesting relationship `students.nests_within(schools)`.

Parameters:

- `group: tisane.Unit` -- the `tisane.Unit` to nest this unit in


## tisane.SetUp

### Initialization
```python
tisane.SetUp(self, name, order=None, cardinality=None, data=None, **kwargs)
```

Creates a data variable for the experiment's environment settings. One example of this is time, since time doesn't belong to any one unit, and is universal across the experiment.

Parameters:
- `name: str` -- the name of the variable. If you have data, this should correspond to the column's name
- `order: list` --
- `cardinality: int` -- the number of unique measurements of the variable
- `data: tisane.data.DataVector` --
- `kwargs` --


# Data Variable Relationships

These data relationships can be applied to all of the variable types we've seen thus far:

 - `tisane.Unit`
 - `tisane.SetUp`
 - `tisane.variable.Nominal`
 - `tisane.variable.Ordinal`
 - `tisane.variable.Numeric`

All of the above variables are subtypes of `tisane.variable.AbstractVariable`, which is where these data variable relationships are defined.

## Causes
```python
tisane.variable.AbstractVariable.causes(self, effect)
```

Adds a `causes` relationship to a data variable. If you have variables `v1` and `v2`, then `v1.causes(v2)` will mean that `v1` causes `v2`.

Parameters:

 - `effect: tisane.variable.AbstractVariable` -- the cause data variable

## Associates With
```python
tisane.variable.AbstractVariable.associates_with(self, variable)
```

Adds a correlation or association relationship to a data variable.

Parameters:

- `variable: tisane.variable.AbstractVariable` -- the variable to be associated with

## Moderates
```python
tisane.variable.AbstractVariable.moderates(self, moderator, on)
```

Adds an interaction relationship to a data variable

Parameters:

- `moderator: ` one of `AbstractVariable` or a list of `AbstractVariable`s -- the variable(s) that moderate(s) the effect of this variable on another variable
- `on: AbstractVariable` -- the variable the effect is on

# Study design: tisane.Design

## Initialization
```python
tisane.Design(self, dv, ivs, source=None)
```
Create an object that represents your study design.

Parameters:

- `dv: tisane.variable.AbstractVariable` -- the dependent variable in your study design
- `ivs: List[tisane.variable.AbstractVariable]` -- a list of the independent variable(s) in your study design
- `source:` one of `os.PathLike` or `pandas.DataFrame` -- either a path to the data for the study or a `DataFrame` containing the data

## tisane.Design.assign_data
```python
tisane.Design.assign_data(self, source)
```

Add a data source to the study design.

Parameters:

- `source:` one of `os.PathLike` or `pandas.DataFrame` -- either a path to the data for the study or a `DataFrame` containing the data

Returns: `self`

# Inference: tisane.infer_statistical_model_from_design
```python
tisane.infer_statistical_model_from_design(design, jupyter=False)
```

Query Tisane to infer a statistical model from a design. This will launch a GUI where you can select further options related to the final model.

Parameters:

- `design: tisane.Design` -- the study design to infer the model from
- `jupyter: bool` -- whether this is launching the GUI in a jupyter notebook or not. If True, this will launch the GUI in the output of the jupyter notebook cell.