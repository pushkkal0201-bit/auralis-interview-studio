"""Auralis 5.3 practical challenges. No user-supplied Python is executed.

A small allowlisted AST *interpreter* evaluates a fixed pure-expression subset of
Python against bounded, predefined test inputs. This intentionally does NOT
support arbitrary Python, imports, loops, recursion, attributes, or filesystem.
"""
import ast
import math
import operator
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from fastapi import HTTPException


class CodingSubmission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    challenge_id: str = Field(min_length=1, max_length=48)
    code: str = Field(min_length=8, max_length=2500)


class EngineeringSubmission(BaseModel):
    model_config = ConfigDict(extra='forbid')
    case_id: Literal['enclosure_supports', 'bend_geometry', 'beam_deflection']
    claimed_result: float = Field(ge=-1e9, le=1e9, allow_inf_nan=False)
    reasoning: str = Field(default='', max_length=2500)


@dataclass(frozen=True)
class Challenge:
    title: str
    description: str
    parameters: tuple[str, ...]
    starter: str
    examples: tuple[tuple[tuple, object], ...]
    hidden: tuple[tuple[tuple, object], ...]
    hint: str


CODING = {
    'sum_numbers': Challenge('Sum a list', 'Return the sum of the integers in nums. Empty lists should return 0.', ('nums',),
        'def solve(nums):\n    return 0', ((([2, 4, 6],),12), (([],),0)), ((([-4, 4, 10],),10), (([0, 0, 0],),0), (([9],),9)), 'A small allowlisted built-in can add list elements.'),
    'reverse_text': Challenge('Reverse text', 'Return the characters of text in reverse order. Preserve spaces and punctuation.', ('text',),
        'def solve(text):\n    return text', ((("Auralis",),"silaruA"), (("a b",),"b a")), ((("",),""), (("racecar",),"racecar"), (("AB!",),"!BA")), 'String slicing has an optional step.'),
    'palindrome': Challenge('Palindrome check', 'Return True when text reads the same forward and backward, exactly as provided (case-sensitive).', ('text',),
        'def solve(text):\n    return False', ((("level",),True), (("hello",),False)), ((("",),True), (("Aa",),False), (("1221",),True)), 'Compare the input with a reversed view.'),
    'range_span': Challenge('Largest gap', 'Return max(nums) - min(nums). All provided test inputs contain at least one integer.', ('nums',),
        'def solve(nums):\n    return 0', ((([4, 12, 7],),8), (([3],),0)), ((([-7, 2, 10],),17), (([0, 0],),0), (([-2, -3],),1)), 'Both the maximum and minimum of a list matter.'),
    'clamp': Challenge('Clamp a number', 'Return value limited to the inclusive interval low to high, where low <= high.', ('value','low','high'),
        'def solve(value, low, high):\n    return value', (((11,0,10),10), ((-3,0,10),0)), (((7,0,10),7), ((0,0,0),0), ((-20,-10,-1),-10)), 'Nested min and max can express clamping.'),
}


SAFE_BUILTINS = {'len':len, 'sum':sum, 'min':min, 'max':max, 'abs':abs, 'sorted':sorted}
BINOPS = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul, ast.Mod:operator.mod,
          ast.FloorDiv:operator.floordiv, ast.Div:operator.truediv}
UNARY = {ast.UAdd:operator.pos, ast.USub:operator.neg, ast.Not:operator.not_}
COMPARATORS = {ast.Eq:operator.eq, ast.NotEq:operator.ne, ast.Lt:operator.lt,
               ast.LtE:operator.le, ast.Gt:operator.gt, ast.GtE:operator.ge}


class ExpressionProblem(ValueError):
    pass


def _bounded(value):
    if isinstance(value, (int,float)):
        if isinstance(value,float) and not math.isfinite(value):
            raise ExpressionProblem('Non-finite arithmetic is not supported.')
        if abs(value)>1e8:raise ExpressionProblem('Arithmetic result is outside the lab limit.')
    if isinstance(value,(str,list,tuple)) and len(value)>256:
        raise ExpressionProblem('Result exceeds the lab size limit.')
    if not isinstance(value,(bool,int,float,str,list,tuple,type(None))):
        raise ExpressionProblem('Unsupported value type.')
    return value


def _eval(node, env, depth=0):
    if depth>14:raise ExpressionProblem('Expression nesting exceeds the limit.')
    n=lambda part:_eval(part,env,depth+1)
    if isinstance(node,ast.Constant):
        if type(node.value) not in (int,float,str,bool,type(None)):raise ExpressionProblem('Unsupported literal.')
        return _bounded(node.value)
    if isinstance(node,ast.Name):
        if node.id not in env:raise ExpressionProblem('Unknown variable.')
        return env[node.id]
    if isinstance(node,(ast.List,ast.Tuple)):
        if len(node.elts)>25:raise ExpressionProblem('Too many literal elements.')
        return _bounded([n(v) for v in node.elts] if isinstance(node,ast.List) else tuple(n(v) for v in node.elts))
    if isinstance(node,ast.BinOp) and type(node.op) in BINOPS:
        left,right=n(node.left),n(node.right)
        # No string/list repetition, or nested expanding operations.
        if type(node.op)==ast.Mult and not all(isinstance(v,(int,float)) for v in (left,right)):
            raise ExpressionProblem('String and list multiplication are not available.')
        try:return _bounded(BINOPS[type(node.op)](left,right))
        except (TypeError,ValueError,ArithmeticError,OverflowError) as exc:raise ExpressionProblem('Invalid arithmetic for these inputs.') from exc
    if isinstance(node,ast.UnaryOp) and type(node.op) in UNARY:
        try:return _bounded(UNARY[type(node.op)](n(node.operand)))
        except (TypeError,ValueError) as exc:raise ExpressionProblem('Unsupported unary operation.') from exc
    if isinstance(node,ast.Compare):
        if any(type(x) not in COMPARATORS for x in node.ops):raise ExpressionProblem('Unsupported comparison.')
        left=n(node.left)
        for op,part in zip(node.ops,node.comparators):
            right=n(part)
            try:ok=COMPARATORS[type(op)](left,right)
            except TypeError as exc:raise ExpressionProblem('Incompatible comparison operands.') from exc
            if not ok:return False
            left=right
        return True
    if isinstance(node,ast.BoolOp) and isinstance(node.op,(ast.And,ast.Or)) and len(node.values)<=5:
        if isinstance(node.op,ast.And):
            result=True
            for part in node.values:
                result=n(part)
                if not result:break
            return result
        result=False
        for part in node.values:
            result=n(part)
            if result:break
        return result
    if isinstance(node,ast.IfExp):return n(node.body if n(node.test) else node.orelse)
    if isinstance(node,ast.Subscript):
        value=n(node.value)
        if not isinstance(value,(str,list,tuple)):raise ExpressionProblem('Only lists and strings can be indexed.')
        if isinstance(node.slice,ast.Slice):
            def part(p):return n(p) if p is not None else None
            args=[part(node.slice.lower),part(node.slice.upper),part(node.slice.step)]
            if any(x is not None and (not isinstance(x,int) or abs(x)>300) for x in args):
                raise ExpressionProblem('Invalid slice bounds.')
            try:return _bounded(value[slice(*args)])
            except ValueError as exc:raise ExpressionProblem('Invalid slice step.') from exc
        idx=n(node.slice)
        if not isinstance(idx,int) or abs(idx)>300:raise ExpressionProblem('Invalid index.')
        try:return _bounded(value[idx])
        except IndexError as exc:raise ExpressionProblem('Index outside the input.') from exc
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in SAFE_BUILTINS:
        if node.keywords or len(node.args) not in (1,2):raise ExpressionProblem('Unsupported built-in argument count.')
        if len(node.args)==2:
            if node.func.id not in ('min','max'):
                raise ExpressionProblem('Two-argument built-in allowed only for min or max.')
            vals=[n(arg) for arg in node.args]
            if not all(type(v) in (int,float) for v in vals):raise ExpressionProblem('Two-argument min/max require numeric values.')
            try:return _bounded(SAFE_BUILTINS[node.func.id](*vals))
            except (TypeError,ValueError) as exc:raise ExpressionProblem('Invalid built-in input.') from exc
        val=n(node.args[0])
        if not isinstance(val,(list,tuple,str)) and node.func.id not in ('abs',):
            raise ExpressionProblem('Built-in expects a list, tuple or string.')
        try:return _bounded(SAFE_BUILTINS[node.func.id](val))
        except (TypeError,ValueError) as exc:raise ExpressionProblem('Invalid argument for built-in.') from exc
    raise ExpressionProblem('Unsupported Python construct. Use a pure return expression.')


def _parse(source,challenge):
    try:root=ast.parse(source,mode='exec')
    except SyntaxError as exc:raise HTTPException(422,'Python syntax error. Check your function definition.') from exc
    if len(list(ast.walk(root)))>90:raise HTTPException(422,'Solution is too complex for the restricted practice runner.')
    if len(root.body)!=1 or not isinstance(root.body[0],ast.FunctionDef):
        raise HTTPException(422,'Submit exactly one function named solve, with a single return statement.')
    func=root.body[0]
    args=func.args
    if func.name!='solve' or func.decorator_list or func.returns or args.vararg or args.kwarg or args.kwonlyargs or args.posonlyargs or args.defaults or args.kw_defaults:
        raise HTTPException(422,'Use a plain def solve(...) function without decorators, defaults, or annotations.')
    if tuple(arg.arg for arg in args.args)!=challenge.parameters or any(a.annotation for a in args.args):
        raise HTTPException(422,'Function parameters must match the challenge specification.')
    if len(func.body)!=1 or not isinstance(func.body[0],ast.Return) or func.body[0].value is None:
        raise HTTPException(422,'Use one return expression. Loops, assignments and imports are not supported.')
    return func.body[0].value


def catalog():
    return {'execution_policy':'Restricted AST expression interpretation; no arbitrary Python execution, subprocesses or network access.',
            'challenges':[{'id':key,'title':v.title,'description':v.description,'parameters':list(v.parameters),
              'starter':v.starter,'examples':[{'input':list(x),'expected':y} for x,y in v.examples], 'hint':v.hint}
              for key,v in CODING.items()], 'engineering_cases':engineering_catalog()}


def evaluate_code(payload:CodingSubmission):
    challenge=CODING.get(payload.challenge_id)
    if not challenge:raise HTTPException(422,'Unknown coding challenge.')
    expression=_parse(payload.code,challenge)
    cases=challenge.examples+challenge.hidden
    output=[]
    for idx,(arguments,expected) in enumerate(cases):
        env=dict(zip(challenge.parameters,arguments))
        try:
            result=_eval(expression,env)
            if not isinstance(result,(bool,int,float,str,list,tuple,type(None))):raise ExpressionProblem('Invalid result type.')
            passed=type(result)==type(expected) and result==expected
            status='pass' if passed else 'fail'
        except ExpressionProblem as exc:
            result=None;passed=False;status='error'
            message=str(exc)
        row={'test':idx+1,'public':idx<len(challenge.examples),'status':status}
        if row['public']:
            row.update({'input':list(arguments),'expected':expected,'actual':result})
        if status=='error':row['message']=message
        output.append(row)
    score=sum(item['status']=='pass' for item in output)
    return {'challenge_id':payload.challenge_id,'passed':score,'total':len(output), 'all_passed':score==len(output),
            'tests':output,'source':'restricted_ast_test_runner','limitations':'Tests demonstrate behavior only for selected inputs. No arbitrary code is executed; this is not full Python.'}


ENGINEERING={
 'enclosure_supports':{'title':'Distribute equipment weight','scenario':'A 180 kg equipment assembly is supported by four ideal equally loaded mounting points. Estimate the STATIC force per support.','quantity':'Load per support','unit':'N','formula':'F_support = mass × 9.81 / number_of_supports','expected':180*9.81/4,'assumptions':'Equal load distribution and static conditions. Verify the real center of gravity, anchor layout, handling loads and structural joints before design approval.'},
 'bend_geometry':{'title':'Plan a 90° sheet-metal bend','scenario':'For a 2 mm steel sheet with a 2 mm inside bend radius and K-factor 0.4, estimate the bend allowance for a 90° bend.','quantity':'Bend allowance','unit':'mm','formula':'BA = (90 × π / 180) × (2 + 0.4 × 2)','expected':math.pi/2*2.8,'assumptions':'K-factor is illustrative; derive actual allowance from forming tests, tooling, grade and springback.'},
 'beam_deflection':{'title':'Estimate support-beam deflection','scenario':'Simplified, simply supported beam with a center load of 1000 N, span 1 m, E=200 GPa and second moment of area I=8×10⁻⁸ m⁴. Find the linear-elastic midpoint deflection.','quantity':'Midpoint deflection','unit':'mm','formula':'δ = P × L³ / (48 × E × I) × 1000','expected':1000/(48*200e9*8e-8)*1000,'assumptions':'Ideal Euler-Bernoulli beam: small deflections, point load, linear elasticity and simple supports. Not a direct certification of the enclosure.'},
}


def engineering_catalog():
    return [{'id':k,**{a:b for a,b in v.items() if a!='expected'}} for k,v in ENGINEERING.items()]


def evaluate_engineering(payload:EngineeringSubmission):
    item=ENGINEERING[payload.case_id]
    target=item['expected'];delta=abs(payload.claimed_result-target)/max(abs(target),1e-12)
    accurate=delta<=0.01
    # Narrative quality must never be inferred automatically from string length.
    return {'case_id':payload.case_id,'quantity':item['quantity'],'expected':round(target,6),'claimed_result':payload.claimed_result,
            'unit':item['unit'],'relative_error_percent':round(delta*100,3),'arithmetic_check':'within_1_percent' if accurate else 'outside_1_percent',
            'formula':item['formula'],'assumptions':item['assumptions'],'reasoning_status':'ungraded_manual_review' if payload.reasoning.strip() else 'not_provided',
            'source':'deterministic_example','limitations':'The 1% threshold checks arithmetic, not engineering tolerance, safety, regulatory compliance or actual fabrication.'}
