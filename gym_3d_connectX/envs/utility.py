import numpy as np


class UtilClass:
    """
    Utility class
    This class gives some useful function for this game.
    To make the classses simple, we separated two classes.

    Attributes
    ----------
    num_grid : int
        Length of a side.
    num_win_seq : int
        The number of sequence necessary for winning.
    win_reward : float
        The reward agent gets when win the game.
    draw_penalty : float
        The penalty agent gets when it draw the game.
    lose_penalty : float
        The penalty agent gets when it lose the game.
    could_locate_reward : float
        The additional reward for agent being able to put the stone.
    couldnt_locate_penalty : float
        The penalty agent gets when it choose the location where the stone cannot be placed.
    time_penalty : float
        The penalty agents gets along with timesteps.
    WIN_A : ndarray
        Player A's judgment constant.
    WIN_B : ndarray
        Player B's judgment constant.
    """

    def __init__(self, num_grid, num_win_seq, win_reward, draw_penalty, lose_penalty,
                 could_locate_reward, couldnt_locate_penalty, time_penalty):
        """
        Parameters
        ----------
        num_grid : int
            Length of a side.
        num_win_seq : int
            The number of sequence necessary for winning.
        win_reward : float
            The reward agent gets when win the game.
        draw_penalty : float
            The penalty agent gets when it draw the game.
        lose_penalty : float
            The penalty agent gets when it lose the game.
        could_locate_reward : float
            The additional reward for agent being able to put the stone.
        couldnt_locate_penalty : float
            The penalty agent gets when it choose the location where the stone cannot be placed.
        time_penalty : float
            The penalty agents gets along with timesteps.
        """
        self.num_grid = num_grid
        self.num_win_seq = num_win_seq
        self.win_reward = win_reward
        self.draw_penalty = draw_penalty
        self.lose_penalty = lose_penalty  # 未使用
        self.could_locate_reward = could_locate_reward
        self.couldnt_locate_penalty = couldnt_locate_penalty
        self.time_penalty = time_penalty  # 未使用
        self.WIN_A = np.full(num_win_seq, 1)
        self.WIN_B = np.full(num_win_seq, -1)

    def resolve_placing(self, wide, depth, player_number, board):
        """
        Places a stone and returns the next state.
        It also returns additional information (and an adjustment reward) based on whether
        or not the user has selected a location where the stone can be placed.

        Parameters
        ----------
        wide : int
            The horizontal coordinates specified by action.
        depth : int
            The vertical coordinate specified by action.
        player_number : int
            The first player's number is 1, and the next is -1.
        board : list[list[list[int]]]
            A three-dimensional array representing the current state.

        Returns
        -------
        reward : float
            The total reward agents get through the transition.
        board : list[list[list[int]]]
            A three-dimensional array representing the current state.
        couldnt_locate : bool
            The flag that is true when it cannot be placed.
        """
        couldnt_locate = False
        for height in range(self.num_grid):
            if board[height][wide][depth] == 0:  # 空いていたら置く
                board[height][wide][depth] = player_number
                reward = self.could_locate_reward
                break
        # その柱(pile)が満杯で置けなかった場合。（height=0~self.num_grid-1 まで埋まっていた場合）
        else:
            reward = -self.couldnt_locate_penalty
            couldnt_locate = True

        return reward, board, couldnt_locate

    def resolve_winning(self, done, player_number, board):
        """
        Return the reward and winner information based on the game result.

        Parameters
        ----------
        done : bool
            The flag of whether the episode has finished or not.
        player_number : int
            The first player's number is 1, and the next is -1.
        board : list[list[list[int]]]
            A three-dimensional array representing the current state.

        Returns
        -------
        done : bool
            The flag of whether the episode has finished or not.
        reward : float
            The total reward agents get through the transition.
        winner : int
            The player number of the winning side.
        """
        reward = 0
        winner = 0
        # stepを実行した側（player_number側）は勝つ以外ありえない
        if done:
            # どちらのプレーヤーが勝利したかにかかわらず、勝利報酬を設定。resolve_placing内で石を置くことによって得た報酬を引いておく。
            reward = self.win_reward - self.could_locate_reward
            winner = player_number
        # 全てのマスが非ゼロにもかかわらず、doneになっていない場合（引き分けの場合）
        elif not (0 in np.array(board).flatten()):
            done = True
            # 引き分けによって課せられる罰。resolve_placing内で石を置くことによって得た報酬を引いておく。
            reward = -self.draw_penalty - self.could_locate_reward
        else:
            pass

        return done, reward, winner

    def is_done(self, cube):
        """
        Judges the end of the game based on the current state of the board.

        Parameters
        ----------
        cube : list[list[list[int]]]
            A three-dimensional array representing the current state.

        Return
        ------
        done : bool
            The flag of whether the episode has finished or not.
        """
        cube = np.array(cube)
        num_stride = self.num_grid - self.num_win_seq + 1

        # 1辺self.num_gridマスの格子内で、1辺self.num_win_seqマスのcubeを1マスずつずらしていく
        for dim_H_stride_id in range(num_stride):
            for dim_W_stride_id in range(num_stride):
                for dim_D_stride_id in range(num_stride):
                    searching_cube = cube[
                                     dim_H_stride_id:dim_H_stride_id + self.num_win_seq,
                                     dim_W_stride_id:dim_W_stride_id + self.num_win_seq,
                                     dim_D_stride_id:dim_D_stride_id + self.num_win_seq
                                     ]

                    # x,y,z軸各方向に垂直な面について解析
                    cube_list = [
                        searching_cube,
                        np.rot90(searching_cube, axes=(0, 1)),
                        searching_cube.T
                    ]

                    # cube内の考えうる全ての二次元平面上でループ
                    for each_cube in cube_list:
                        for plane in each_cube:
                            # 2次元平面上でビンゴしていないか確認
                            if self.is_end_on_2d_plane(plane):
                                return True

                    # 立体的な斜め
                    if self.is_diag_on_3d_cube(each_cube):
                        return True

        return False

    def is_end_on_2d_plane(self, org_plane):
        """
        Determine if there are N balls lined up in an N x N two-dimensional array.

        Parameters
        ----------
        org_plane : ndarray
            An array containing the current state of the plane.
        Return
        ------
        is_end_on_2d_plane : bool
            The flag whether a row is aligned on a plane.
        """
        assert org_plane.shape == (self.num_win_seq, self.num_win_seq)

        # 行・列
        for plane in [org_plane, org_plane.T]:
            for row in plane:
                if all(row == self.WIN_A) or all(row == self.WIN_B):
                    return True

        # 斜め
        if abs(np.trace(org_plane)) == self.num_win_seq or abs(np.trace(np.fliplr(org_plane))) == self.num_win_seq:
            return True

        return False

    def is_diag_on_3d_cube(self, org_cube):
        """
        Determine whether or not N balls are lined up on the three-dimensional array of N x N x N
        on the three-dimensional diagonal.

        Parameters
        ----------
        org_cube : ndarray
            An array containing the current state of the cube.

        Return
        ------
        is_diag_on_3d_cube : bool
            The flag whether a row is aligned on a 3D object.
        """
        assert org_cube.shape == (self.num_win_seq, self.num_win_seq, self.num_win_seq)

        for cube in [org_cube, np.rot90(org_cube, axes=(1, 2)), np.rot90(org_cube, axes=(0, 1)),
                     np.rot90(org_cube.T, axes=(0, 1))]:

            oblique_elements = np.empty(0)
            for f in range(self.num_win_seq):
                for a in range(self.num_win_seq):
                    for b in range(self.num_win_seq):
                        if f == a and a == b and f == b:
                            oblique_elements = np.append(oblique_elements, cube[f][a][b])

            if (all(oblique_elements == np.full(self.num_win_seq, 1)) or all(
                    oblique_elements == np.full(self.num_win_seq, -1))):
                return True

        return False

    def base_change(self, value, base):
        """
        Convert the input to the decimal number specified by base.

        Parameters
        ----------
        value : int
            The action expressed as a number between 1 ~ self.num_grid ** 2.
        base : int
            Specifies the decimal value to be converted.

        Return
        ------
        base_change : str
            A string that converts the input to the decimal number specified by base.
        """
        if value // base:
            return self.base_change(value // base, base) + str(value % base)
        return str(value % base)

    def is_game_end(self, player_number, board):
        """
        Judges the end of the game based on the current state of the board,
        and returns the reward and winner information according to the result of the game.

        Parameters
        ----------
        player_number : int
            The first player's number is 1, and the next is -1.
        board : list[list[list[int]]]
            A three-dimensional array representing the current state.

        Returns
        -------
        is_end : bool
            The flag of whether the episode has finished or not.
        reward : float
            The total reward agents get through the transition.
        winner : int
            The player number of the winning side.
        """
        done = self.is_done(board)
        is_end, reward, winner = self.resolve_winning(done, player_number, board)

        return is_end, reward, winner
